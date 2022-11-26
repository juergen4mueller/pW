import platform
import glob

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

get_serial_port()
get_ip_address()


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