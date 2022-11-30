import time
import cv2
import threading
import queue
import serial
import io
from datetime import datetime
from pyzbar.pyzbar import decode
import sys
import os
import sqlite3
import platform
import glob
import socket

from dash import dash, dcc, html, callback_context
from flask import Flask, Response, request
import dash_bootstrap_components as dbc


def get_ip_address():
    """Ermittlung der IP-Adresse im Netzwerk
    Returns:
        str: lokale IP-Adresse
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_ip = "127.0.0.1"
    try:
        s.connect(("8.8.8.8", 80))
        socket_ip = s.getsockname()[0]
    except:
        print("no internet")
    finally:
        s.close()
    print("IP adress:", socket_ip)
    return socket_ip


def get_serial_port():
    """Serial Port für GPS abhängig vom Gerät ermitteln
    Implementierung für Windows steht noch aus
    Dropdown kann hier noch für mehr Optionen sorgen

    Returns:
        _type_: _description_
    """
    serialPort = None
    system = platform.system()
    if system == "Darwin":
        serialPort = glob.glob("/dev/tty.usb*")[0]

    elif system == "Linux":
        sps = glob.glob("/dev/ttyUSB*")
        if len(sps) >= 1:
            serialPort = sps[0]
        else:
            sps = glob.glob(" /dev/ttyACM**")
            if len(sps) >= 1:
                serialPort = sps[0]

    print("Seial port detected:", serialPort)
    return serialPort


class GPS:
    """Hält die GPS-Daten vor"""

    def __init__(self) -> None:
        self.status = "V"
        self.v_kmh = 0
        self.v_kn = 0
        self.lon = 0
        self.lat = 0
        self.date_time = None
        self.dir = 0
        self.sats_used = 0
        self.alti = 0

    @staticmethod
    def convert_coord(NMEA_coord: str):
        """_summary_

        Args:
            NMEA_coord (str): GPS-String von NMEA-Empfänger DDDMM.MMM

        Returns:
            floaat: Gibt des Wert in Grad uzrück
        """
        gm, _, m = NMEA_coord.partition(".")
        grad = gm[:-2]
        min = gm[-2:] + "." + m
        coord = int(grad) + (float(min)) / 60
        return round(coord, 6)

    def out(self):
        """Ausgabe der GPS-Daten über die Konsole"""
        print("GPS data:")
        print("Time", self.date_time)
        print("Pos: ", self.lon, self.lat)
        print("speed:", self.v_kmh, "km/h")
        print("Dir: ", self.dir)
        print("Alti:", self.alti)
        print("SATs used: ", self.sats_used)


gps = GPS()


class QR:
    """Infos des im Bild gefundenen QR-Codes"""

    def __init__(self, data) -> None:
        self.data = data
        self.posx = 0
        self.posy = 0

    @staticmethod
    def calc_code_position(frame, rect):
        """Ermittelt die Position des Codes im Bild

        Args:
            frame (_type_): Bild in dem der Code gefunden wurde
            rect (_type_): Rechteck-Koordinaten des Codes

        Returns:
            _type_: Position (x,y) im Bild (Werte -1 ... 1)
        """
        x_val = 0
        y_val = 0
        f_height, f_width, _ = frame.shape
        left, top, height, width = rect
        codeCenter = (left + width // 2, top + height // 2)
        frameCenter = (f_width // 2, f_height // 2)
        x_val = round((codeCenter[0] - frameCenter[0]) / frameCenter[0], 3)
        y_val = round((codeCenter[1] - frameCenter[1]) / frameCenter[1], 3)
        return (x_val, y_val)

    def set_pos(self, pos):
        self.posx, self.posy = pos

    def debug(self):
        """Ausgabe der Code-Daten auf der Konsole"""
        print(20 * "*")
        print("QR-Code Info:")
        print(self.data)
        print("Offset: ", self.posx, ":", self.posy)
        print(20 * "*")


class DL:
    """Funktion um die Daten zu speichern"""

    def __init__(self, filename="db.sqlite", timeBetween=20) -> None:
        folder = sys.path[0]
        self.timeBetween = timeBetween
        self.seenCodes = {}
        self.dbPath = os.path.join(folder, filename)
        # initialise db
        print(self.dbPath)
        self.con = sqlite3.connect(self.dbPath)
        self.cur = self.con.cursor()
        sql_create_table = """CREATE TABLE IF NOT EXISTS "loggings" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "code" TEXT,
                        "posx" NUMERIC,
                        "posy" NUMERIC,
                        "datetime",
                        "lat" NUMERIC,
                        "lon" NUMERIC,
                        "speed" NUMERIC,
                        "direction" NUMERIC,
                        PRIMARY KEY("id" AUTOINCREMENT)
                        );"""
        self.cur.execute(sql_create_table)
        self.con.commit()

    def log_item(self, qrQode: QR):
        if gps.status == "A":
            if self.seenCodes.get(qrQode.data, 0) <= time.time() - self.timeBetween:
                sql_cmd = "insert into loggings (code, posx, posy, datetime, lat, lon, speed, direction) values (?, ?, ?, ?, ?, ?, ?, ?) "
                self.cur.execute(
                    sql_cmd,
                    (
                        qrQode.data,
                        qrQode.posx,
                        qrQode.posy,
                        gps.date_time,
                        gps.lat,
                        gps.lon,
                        gps.v_kmh,
                        gps.dir,
                    ),
                )
                self.con.commit()
                print("neuer Eintrag")
            else:
                print("zu schnell")
        else:
            print("GPS Signal weak")
        self.seenCodes[qrQode.data] = time.time()

    def close(self):
        self.con.close()


gpsActive = False


def getGpsPos():
    global gpsActive
    """ Stream vom GPS-Empfänger einlesen, auswerten und ablegen der Daten im gps-Objekt
    """
    sp = get_serial_port()
    ser = serial.Serial(sp, 9600, timeout=5.0)
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
    print("Starte GPS Auswertung")
    while gpsActive:
        try:
            line = sio.readline()
            update = False
            if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                update = True
                params = line.split(",")
                gps.status = params[2]
                if gps.status == "A":
                    if params[4] == "N":
                        gps.lat = GPS.convert_coord(params[3])
                    else:
                        gps.lat = 0 - GPS.convert_coord(params[3])
                    if params[6] == "E":
                        gps.lon = GPS.convert_coord(params[5])
                    else:
                        gps.lon = 0 - GPS.convert_coord(params[5])
                    gps.v_kn = float(params[7])
                    gps.v_kmh = round(gps.v_kn * 1.852, 1)
                    try:
                        dir = float(params[8])
                    except:
                        dir = None
                    gps.dir = dir
                    hh = int(params[1][:2])
                    mm = int(params[1][2:4])
                    ss = int(params[1][4:6])
                    dd = int(params[9][:2])
                    MM = int(params[9][2:4])
                    yy = int(params[9][4:6]) + 2000
                    gps.date_time = datetime(yy, MM, dd, hh, mm, ss)
            elif line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                update = True
                params = line.split(",")
                if params[6] == "1":
                    gps.sats_used = int(params[7])
                    gps.alti = round(float(params[9]), 1)
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            break
    ser.close()


worker_gps = threading.Thread(None, getGpsPos, daemon=True)


def start_gps():
    global gpsActive
    gpsActive = True
    worker_gps.start()


def stop_gps():
    global gpsActive
    gpsActive = False


class Camera:
    """A class for the camera

    Args:
    skip_frame: number of frames to skip while recording
    cam_number: which camera should be used. Defaults to 0.

    Attributes
    --------

    VideoCapture: Class to get the video feed
    _imgsize: size of the image

    Methods
    --------
    get_frame(): returns current frame, recorded by the camera
    show_frame(): plots the current frame, recorded by the camera
    get_jpeg(): returns the current frame as .jpeg/raw bytes file
    save_frame(): saves the frame at the given path under the given name
    release(): releases the camera, so it can be used again and by other programs
    """

    def __init__(self, skip_frame=2, cam_number=0, thread=False, fps=30):
        self.skip_frame = skip_frame
        self.VideoCapture = cv2.VideoCapture(cam_number)  # , cv2.CAP_V4L) #,
        self.VideoCapture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.VideoCapture.set(cv2.CAP_PROP_FPS, fps)
        self._imgsize = (
            int(self.VideoCapture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.VideoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        if thread:
            self._queue_drive = queue.Queue(maxsize=1)
            self._thread = threading.Thread(target=self._reader, daemon=True)
            self._thread.start()

    def set_image_size(self, width, height):
        print("New image size:", width, "x", height)

        self.VideoCapture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.VideoCapture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def _reader(self):
        """Put current frame recorded by the camera to the Queue-Object."""
        while True:

            frame = self.get_frame()

            if not self._queue_drive.empty():
                try:
                    self._queue_drive.get_nowait()
                except self._queue_drive.Empty:
                    pass
            self._queue_drive.put(frame)

    def read(self):
        """Returns current frame hold in Queue-Object.

        Returns:
            numpy array: returns current frame as numpy array
        """
        return self._queue_drive.get()

    def get_frame(self):
        """Returns current frame recorded by the camera

        Returns:
            numpy array: returns current frame as numpy array
        """
        if self.skip_frame:
            for i in range(int(self.skip_frame)):
                _, frame = self.VideoCapture.read()
        _, frame = self.VideoCapture.read()
        frame = cv2.flip(frame, -1)
        return frame

    def get_jpeg(self, frame=None):
        """Returns the current frame as .jpeg/raw bytes file

        Args:
            frame (list): frame which should be saved.

        Returns:
            bytes: returns the frame as raw bytes
        """
        if frame is None:
            frame = self.get_frame()
            frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            height, width, _ = frame.shape
            text = str(width) + "x" + str(height)
            frame = cv2.putText(
                frame, text, (10, 40), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 1
            )
        _, x = cv2.imencode(".jpeg", frame)
        return x.tobytes()

    def save_frame(self, path: str, name: str, frame=None):
        """Saves the current frame under the given path and filename

        Args:
            path (str): path where the file should be saved
            name (str): name under which the file should be saved
            frame (np.array, optional): frame which should be saved.
                                        If None then the current frame recorded by the camera gets saved.
                                        Defaults to None.
        """
        if frame is None:
            frame = self.get_frame()
        cv2.imwrite(path + name, frame)

    def release(self):
        """Releases the camera so it can be used by other programs."""
        self.VideoCapture.release()

    def get_image_bytes(self):
        """Generator for the images from the camera for the live view in dash

        Yields:
            [bytes]: Bytes string with the image information
        """
        while True:
            jepg = self.get_jpeg()

            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jepg + b"\r\n\r\n"
            )
            time.sleep(0.01)


cam = Camera(thread=True, fps=30)


server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    meta_tags=[
        {"name": "viewport"},
        {"content": "width = device,width, initial-scale=1.0"},
    ],
)
app.layout = html.Img("http://127.0.0.1/video_feed")


@server.route("/video_feed")
def video_feed():
    """Will return the video feed from the camera

    Returns:
        Response: Response object with the video feed
    """
    return Response(
        cam.get_image_bytes(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


host = get_ip_address()


def runVideoServer(host=host, port=8090):
    print("starting App ...")
    app.run_server(debug=False, host="localhost", port=port)
    print("App destroyed")


videoServer = threading.Thread(None, runVideoServer, daemon=True)


def startWebcam():
    print("starting video server ...")
    videoServer.start()

    return cam


def stopWebcam():
    cam.release()


loggerRunning = False


def runLogger(run):
    global loggerRunning
    loggerRunning = run


def start_qr_dedection():
    """Routine um QR-Codes zu erkennen und die Daten dann abzulegen"""
    gps_ready_alt = False
    filename = (
        str(datetime.now())[:-7].replace("-", "").replace(":", "").replace(" ", "_")
        + "_log.sqlite"
    )
    logger = DL(filename=filename)
    start_gps()
    try:
        while True:
            time.sleep(0.01)
            if loggerRunning:
                if gps_ready_alt == False and gps.status == "A":
                    gps_ready_alt = True
                if gps_ready_alt == True and gps.status != "A":
                    gps_ready_alt = False
                frame = cam.get_frame()
                # frame = cv2.resize(frame, dsize=(0, 0), fx=0.4, fy=0.4)
                codes = decode(frame)
                for code in codes:
                    qrCode = QR(code.data.decode())
                    qrCode.set_pos(qrCode.calc_code_position(frame, code.rect))
                    # qrCode.debug()
                    logger.log_item(qrCode)
            else:
                pass

    except KeyboardInterrupt:
        print("Clean and exit program")
        logger.close()


if __name__ == "__main__":
    runLogger(True)
    start_qr_dedection()
