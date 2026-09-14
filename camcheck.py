import usb.core
import usb.util

# Find the Microsoft VX-1000 webcam
dev = usb.core.find(idVendor=0x045e, idProduct=0x00f7)

if dev is None:
    print("Error: Camera not found.")
else:
    print("Success: Camera hardware detected.")
    
    try:
        # Try to get device configuration without calling active driver check first
        cfg = dev.get_active_configuration()
        print(f"Active configuration: {cfg}")
    except Exception as e:
        print(f"Direct configuration access blocked: {e}")
        
        # Alternative method using custom open / backend hook if available
        try:
            # Re-initialize device handle manually
            if hasattr(dev, '_ctx') and dev._ctx:
                print("USB context exists, trying direct interface claim...")
        except Exception as inner_e:
            print(f"Bypass failed: {inner_e}")
