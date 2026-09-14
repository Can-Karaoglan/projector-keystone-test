import usb.core

dev = usb.core.find(idVendor=0x045e, idProduct=0x00f7)
if dev is None:
    print("Device not found")
else:
    try:
        active = dev.is_kernel_driver_active(0)
        print("Kernel server active:", active)
    except Exception as e:
        print("An error occurred:", e)
