import usb.core
import usb.util

# Find the Microsoft VX-1000 webcam
dev = usb.core.find(idVendor=0x045e, idProduct=0x00f7)

if dev is None:
    print("Error: Camera not found.")
else:
    print("Success: Camera hardware detected.")
    
    # Iterate through configurations and interfaces to claim endpoints manually
    for cfg in dev:
        print(f"Configuration value: {cfg.bConfigurationValue}")
        for intf in cfg:
            print(f"Interface: {intf.bInterfaceNumber}, Alternate: {intf.bAlternateSetting}")
            try:
                # Attempt to claim interface directly without kernel detach
                if dev.is_kernel_driver_active(intf.bInterfaceNumber):
                    dev.detach_kernel_driver(intf.bInterfaceNumber)
                usb.util.claim_interface(dev, intf.bInterfaceNumber)
                print(f"Successfully claimed interface {intf.bInterfaceNumber}!")
            except Exception as e:
                print(f"Failed to claim interface {intf.bInterfaceNumber}: {e}")
