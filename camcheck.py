import usb.core
import usb.util

# Find the Microsoft VX-1000 webcam
dev = usb.core.find(idVendor=0x045e, idProduct=0x00f7)

if dev is None:
    print("Error: Camera not found on the USB bus.")
else:
    print("Success: Camera detected.")
    
    # Check and detach kernel driver if active
    if dev.is_kernel_driver_active(0):
        try:
            dev.detach_kernel_driver(0)
            print("Kernel driver detached successfully.")
        except usb.core.USBError as e:
            print(f"Failed to detach kernel driver: {e}")

    try:
        # Set the active configuration
        dev.set_configuration()
        print("Device configuration set successfully.")
    except usb.core.USBError as e:
        print(f"Access Denied / USB Error: {e}")
