import usb.core

# Tüm USB cihazlarını bul
devices = usb.core.find(find_all=True)

found = False
for cfg in devices:
    found = True
    print(f"Vendor ID: {hex(cfg.idVendor)}, Product ID: {hex(cfg.idProduct)}")
    
if not found:
    print("Cannot detect any USB devices. :/")
