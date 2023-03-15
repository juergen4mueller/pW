import eel
import time
import threading
import sys
import os
import persWerb

eel.init(os.path.join(sys.path[0], "web"))


import socket


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


@eel.expose  # Expose this function to Javascript
def startApp():
    persWerb.runLogger(False)
    app_running = True
    print("start App")


@eel.expose
def stopApp():
    persWerb.runLogger(False)
    print("stopp app")


@eel.expose
def setResolution(width, height):
    persWerb.cam.set_image_size(width, height)


counter = 0


def update_gps_data():
    while True:
        if persWerb.gps.status == "A":
            # Daten valide, update
            eel.set_Gps_values(
                persWerb.gps.lat, persWerb.gps.lon, persWerb.gps.v_kmh, persWerb.gps.dir
            )
        else:
            eel.set_Gps_values(0, 0, 0, 0)
        time.sleep(1)


host = get_ip_address()


def run_eel():
    eel.start(
        "index.html",
        host=host,
        mode="chrome",
        port=8080,
        size=(1200, 800),
        position=(0, 0),
    )


thread_gps_update = threading.Thread(target=update_gps_data, daemon=True)
thread_qr_finder = threading.Thread(target=persWerb.start_qr_dedection, daemon=True)


if __name__ == "__main__":
    thread_gps_update.start()
    persWerb.startWebcam()
    thread_qr_finder.start()
    time.sleep(2)
    print("starting eel ...")
 
    
    # entweder eel starten und bei schließen des Fenster App beenden
    eel.start(
        "index.html",
        host=host,
        mode="chrome",
        port=8080,
        size=(1200, 800),
        position=(0, 0),
    )
    
    """
    # oder run forever
    thread_eel = threading.Thread(target=run_eel, daemon=True).start()
    while True:
        time.sleep(0.1)
    """
