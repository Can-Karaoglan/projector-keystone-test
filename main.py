import cv2
import numpy as np
import usb.core
import usb.util

def initialize_usb_camera():
    print("Sistemdeki USB cihazları taranıyor...")
    all_devs = list(usb.core.find(find_all=True))
    
    dev = None
    for d in all_devs:
        print(f"Bulunan Cihaz -> Vendor ID: {hex(d.idVendor)}, Product ID: {hex(d.idProduct)}")
        if d.idVendor == 0x045e:  # Microsoft VX-1000
            dev = d
            break
            
    # Eğer özel ID bulunamazsa ilk bulunan USB kamerayı dene
    if dev is None and len(all_devs) > 0:
        dev = all_devs[0]

    if dev is None:
        return None, None

    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
    except Exception:
        pass

    try:
        dev.set_configuration()
    except Exception:
        pass
        
    try:
        cfg = dev.get_active_configuration()
    except Exception:
        cfg = dev[0]
        
    intf = cfg[(0, 0)]

    ep_in = None
    for ep in intf:
        if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
            ep_in = ep
            break

    return dev, ep_in

def get_usb_camera_frame(dev, ep_in):
    """
    Reads raw USB packets, strips UVC headers, isolates MJPEG frames,
    and decodes them into OpenCV-compatible numpy arrays.
    """
    buffer = bytearray()
    while True:
        try:
            # Okuma boyutunu endpoint'e göre güvenli alıyoruz
            packet_size = max(ep_in.wMaxPacketSize, 1024)
            data = dev.read(ep_in.bEndpointAddress, packet_size, timeout=500)
            buffer.extend(data)
            
            start = buffer.find(b'\xff\xd8')
            end = buffer.find(b'\xff\xd9')
            
            if start != -1 and end != -1 and end > start:
                jpg_data = buffer[start:end+2]
                del buffer[:end+2]
                
                frame_arr = np.frombuffer(jpg_data, dtype=np.uint8)
                frame = cv2.imdecode(frame_arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    return frame
        except usb.core.USBError as e:
            # Zaman aşımı veya geçici okuma hatalarında döngüyü kırmadan devam et
            if e.errno == 110: # ETIMEDOUT
                continue
            else:
                break
    return None

def draw_grid_and_markers(frame, h, w, show_full_grid=True):
    """
    Draws non-intrusive calibration shapes, corners, center markers, 
    and a subtle grid pattern onto the frame without disrupting media playback.
    """
    if show_full_grid:
        grid_color = (40, 120, 40)
        for x in range(0, w, 80):
            cv2.line(frame, (x, 0), (x, h), grid_color, 1)
        for y in range(0, h, 60):
            cv2.line(frame, (0, y), (w, y), grid_color, 1)

    corner_color = (0, 255, 0)
    cv2.circle(frame, (40, 40), 8, corner_color, -1)
    cv2.circle(frame, (w - 40, 40), 8, corner_color, -1)
    cv2.circle(frame, (40, h - 40), 8, corner_color, -1)
    cv2.circle(frame, (w - 40, h - 40), 8, corner_color, -1)

    cv2.circle(frame, (w // 2, 40), 6, (255, 0, 0), -1)
    cv2.circle(frame, (w // 2, h - 40), 6, (255, 0, 0), -1)
    cv2.circle(frame, (40, h // 2), 6, (255, 0, 0), -1)
    cv2.circle(frame, (w - 40, h // 2), 6, (255, 0, 0), -1)
    cv2.circle(frame, (w // 2, h // 2), 10, (0, 0, 255), -1)

def detect_calibration_markers(frame):
    """
    Detects the green calibration corner markers using HSV filtering and contour analysis.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    points = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 15:
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                points.append((cX, cY))
                
    if len(points) >= 4:
        points = np.array(points, dtype="float32")
        s = points.sum(axis=1)
        rect = np.zeros((4, 2), dtype="float32")
        rect[0] = points[np.argmin(s)]
        rect[3] = points[np.argmax(s)]
        
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]
        rect[2] = points[np.argmax(diff)]
        return rect
        
    return None

def main():
    print("Searching for available USB camera devices via PyUSB...")
    dev, ep_in = initialize_usb_camera()
    
    if dev is None or ep_in is None:
        print("NOTIFICATION: Camera could not be detected!")
        print("Please ensure the camera is properly connected, libusb is installed, and Termux has USB permissions.")
        return

    print("USB Camera successfully initialized via raw PyUSB layer.")

    is_calibrated = False
    blocked_counter = 0
    prev_gray = None
    dst_pts = None
    cached_perspective_matrix = None
    calibration_cooldown = 0

    while True:
        frame = get_usb_camera_frame(dev, ep_in)
        if frame is None:
            print("Error: Failed to grab frame from the USB device.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        avg_brightness = np.mean(gray)
        if avg_brightness < 12:
            blocked_counter += 1
            if blocked_counter > 20:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, h - 50), (w, h), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
                cv2.putText(frame, "NOTIFICATION: Projector screen not detected! Remove obstruction or realign camera.", 
                            (15, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
            
            cv2.imshow("Automated Keystone Correction System", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue
        else:
            blocked_counter = 0

        motion_detected = False
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            non_zero_count = np.count_nonzero(diff > 30)
            if non_zero_count > (w * h * 0.03):
                motion_detected = True
        
        prev_gray = gray.copy()

        if not is_calibrated or motion_detected or cached_perspective_matrix is None:
            if calibration_cooldown == 0:
                src_pts = detect_calibration_markers(frame)
                if src_pts is not None:
                    if dst_pts is None:
                        dst_pts = np.array([
                            [40, 40],
                            [w - 40, 40],
                            [40, h - 40],
                            [w - 40, h - 40]
                        ], dtype="float32")
                    
                    cached_perspective_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                    is_calibrated = True
                    calibration_cooldown = 30
            else:
                calibration_cooldown -= 1

        draw_grid_and_markers(frame, h, w, show_full_grid=True)

        if cached_perspective_matrix is not None:
            warped = cv2.warpPerspective(frame, cached_perspective_matrix, (w, h))
            cv2.imshow("Automated Keystone Correction System", warped)
        else:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 40), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            cv2.putText(frame, "NOTIFICATION: Initializing grid alignment... Searching for projection area.", 
                        (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.imshow("Automated Keystone Correction System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
