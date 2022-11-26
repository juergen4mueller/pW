import serial
import io
import time
from datetime import datetime
import threading
import cv2
from pyzbar.pyzbar import decode
import sys
import os
import sqlite3
import platform
import glob


import logging

def get_serial_port():
    serialPort = None
    system = platform.system()
    if system =="Darwin":
        serialPort = glob.glob("/dev/tty.usb*")[0]
       
    elif system =="Linux":
        sps = glob.glob("/dev/ttyUSB*")
        if sps.count() >=1:
            serialPort =sps[0]
        else:
            sps = glob.glob(" /dev/ttyACM**")
            if sps.count() >=1:
                serialPort =sps[0]
        
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


col_gn = (10, 0, 0, 0)
col_rt = (0, 10, 0, 0)
col_bl = (0, 0, 10, 0)
col_ws = (0, 0, 0, 10)
col_sw = (0, 0, 0, 0)

#neo = Neopixel(board.D10, 4)
# LED 0 RPi Programm läuft
# LED 1 Status GPS rot: nicht bereit, grün: ok
# LED 2 blinkt bei jeder Bildauswertung
# LED 3 blinkt bei Empfang von NMEA-Paketen


def getGpsPos():
    """GPS-Empfänger über USB einlesen und auswerten"""
    serialPort = get_ser
    ser = serial.Serial("/dev/ttyACM0", 9600, timeout=5.0)
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
    print("Starte GPS Auswertung")
    while True:
        try:
            line = sio.readline()
            if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
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
                params = line.split(",")
                if params[6] == "1":
                    gps.sats_used = int(params[7])
                    gps.alti = round(float(params[9]), 1)
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            break

def main():
    """Routine um QR-Codes zu erkennen und die Daten dann abzulegen"""
    gps_ready_alt = False
    worker_gps = threading.Thread(None, getGpsPos, daemon=True)

    filename = (
        str(datetime.now())[:-7].replace("-", "").replace(":", "").replace(" ", "_")
        + "_log.sqlite"
    )
    logger = DL(filename=filename)
    worker_gps.start()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error starting stream")
    try:
        while True:
            if gps_ready_alt == False and gps.status == "A":
                gps_ready_alt = True
            if gps_ready_alt == True and gps.status != "A":
                gps_ready_alt = False
            ret, frame = cap.read()
            frame = cv2.resize(frame, dsize=(0, 0), fx=0.4, fy=0.4)
            codes = decode(frame)
            for code in codes:
                qrCode = QR(code.data.decode())
                qrCode.set_pos(qrCode.calc_code_position(frame, code.rect))
                # qrCode.debug()
                logger.log_item(qrCode)

    except KeyboardInterrupt:
        print("Clean and exit program")
        cap.release()
        logger.close()


def simple_logger():
    """um einen GPS-Trace aufzuzeichnen"""
    worker_gps = threading.Thread(None, getGpsPos, daemon=True)
    logger = DL("trace.sqlite", 2)
    worker_gps.start()
    try:
        while True:
            qrCode = QR("logging_only")
            logger.log_item(qrCode)
            time.sleep(10)
    except KeyboardInterrupt:
        logger.close()



if __name__ == "__main__":
     main()
