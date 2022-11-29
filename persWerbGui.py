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


app_running = False

@eel.expose  # Expose this function to Javascript
def startApp():
    global app_running
    app_running = True
    print("start App")


@eel.expose
def stopApp():
    global app_running
    app_running = False
    print("stopp app")

@eel.expose
def setResolution(width,height):
    persWerb.cam.set_image_size(width, height)
    

counter = 0


def updater():
    global counter
    while True:
        if app_running:
            counter += 1
            eel.set_Kompass_value(str(counter))
        time.sleep(0.005)


runner = threading.Thread(target=updater, daemon=True)


if __name__ == "__main__":
    host = get_ip_address()
    runner.start()
    persWerb.startWebcam()
    time.sleep(2)
    print("starting eel ...")
    eel.start(
        "index.html", host=host, mode="chrome", port=8080, size=(800, 480), position=(0, 0)
    )
