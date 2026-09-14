python3 -c "import usb.core; print([hex(d.idVendor) + ':' + hex(d.idProduct) for d in usb.core.find(find_all=True)])"
