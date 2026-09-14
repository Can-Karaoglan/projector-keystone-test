import usb.core
import usb.util

dev = usb.core.find(idVendor=0x045e, idProduct=0x00f7)

if dev is None:
    print("Can't find any camera.")
else:
    print("Camera found:", dev)
    try:
        dev.set_configuration()
        print("Configuration successfully picked!")
    except Exception as e:
        print("Connection error (Access Denied):", e)
