import eel
import time
import threading
import sys
import os
import mycam

eel.init(os.path.join(sys.path[0], "web"))


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
    mycam.cam.set_image_size(width, height)
    

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
    runner.start()
    mycam.startWebcam()
    time.sleep(2)
    print("starting eel ...")
    eel.start(
        "index.html", host="localhost", mode="chrome", port=8080, size=(800, 480), position=(0, 0)
    )
