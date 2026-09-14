python3 -c "import usb.core; dev = usb.core.find(idVendor=0x045e, idProduct=0x00f7); print(dev.is_kernel_driver_active(0) if dev else 'Device not found.')"
