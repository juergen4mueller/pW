import platform
import glob

system = platform.system()
if system =="Darwin":
    serialPort = glob.glob("/dev/tty.usb*")[0]


elif system =="Linux":
    serialPort = glob.glob("/dev/ttyUSB*")[0]



"""
unter Linux definierten Namen für USB-Serial-Adapter festlegen:
dmesg | grep ttyUSB                                                             # liste aller USB-Serial-Adapter
udevadm info --name=/dev/ttyUSB0 --attribute-walk       # alle Parameter von USB_Device anzeigen

--> suche nach:
- idProduct : 7523
- idVendor : 1a86

file anlegen:
sudo nano /etc/udev/rules.d/10-usb-serial.rules

für jeden USB-Serial-Adapter einen Namen zuweisen:
SUBSYSTEM=="tty", ATTRS{idProduct}=="7523", ATTRS{idVendor}=="1a86", SYMLINK+="ttyUSB_DEVICE1"

Regel direkt anwenden:
sudo udevadm trigger

"""