import cv2
import numpy as np

def find_working_camera():
    indices = [-1, 0, 1, 2, 3, 4, 5]
    for index in indices:
        try:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    cap.release()
                    return index
                cap.release()
        except Exception:
            continue
    return None

def detect_calibration_markers(frame):
    """
    Kameranın gördüğü duvardaki/perdedeki yeşil referans dairelerini (köşeleri) tespit eder.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Yeşil renk aralığı (kalibrasyon daireleri için)
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    points = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 10:  # Çok küçük gürültüleri ele
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                points.append((cX, cY))
                
    # Tam 4 köşe bulunduysa bunları sol-üst, sağ-üst, sol-alt, sağ-alt olarak sırala
    if len(points) == 4:
        points = np.array(points, dtype="float32")
        # Sıralama mantığı: x+y toplamı en küçük sol-üst, x-y farkı en az olan sağ-üst vb.
        s = points.sum(axis=1)
        rect = np.zeros((4, 2), dtype="float32")
        rect[0] = points[np.argmin(s)]     # Sol-üst
        rect[3] = points[np.argmax(s)]     # Sağ-alt
        
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]    # Sağ-üst
        rect[2] = points[np.argmax(diff)]    # Sol-alt
        return rect
        
    return None

def main():
    print("Searching for available camera devices...")
    cam_index = find_working_camera()
    
    if cam_index is None:
        print("NOTIFICATION: Camera could not be detected!")
        print("Please ensure the camera is properly connected, the USB hub has enough power, or check Termux permissions.")
        return

    print(f"Camera successfully found at index: {cam_index}")
    cap = cv2.VideoCapture(cam_index)

    is_calibrated = False
    blocked_counter = 0
    prev_gray = None
    dst_pts = None

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Error: Failed to grab frame from the camera.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # 1. Error Management: Check if camera is blocked or dark
        avg_brightness = np.mean(gray)
        if avg_brightness < 10:
            blocked_counter += 1
            if blocked_counter > 25:
                cv2.putText(frame, "NOTIFICATION: Camera blocked or screen not detected!", 
                            (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.imshow("Projector Keystone Test", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue
        else:
            blocked_counter = 0

        # 2. Motion and Angle Change Detection (Motion Trigger)
        motion_detected = False
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            non_zero_count = np.count_nonzero(diff > 25)
            if non_zero_count > (w * h * 0.02):
                motion_detected = True
        prev_gray = gray.copy()

        # 3. Smart Calibration and Reference Shapes
        if not is_calibrated or motion_detected:
            # Projektör ekranına yansıtılacak referans köşe daireleri çizilir
            cv2.circle(frame, (40, 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (w - 40, 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (40, h - 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (w - 40, h - 40), 6, (0, 255, 0), -1)
            is_calibrated = True

        # 4. Keystone Correction (Perspective Warp) Application
        # Kameradan gelen görüntüdeki yeşil daireleri bulmaya çalış
        src_pts = detect_calibration_markers(frame)
        if src_pts is not None:
            # Hedef düzgün dikdörtgen koordinatları
            if dst_pts is None:
                dst_pts = np.array([
                    [40, 40],
                    [w - 40, 40],
                    [40, h - 40],
                    [w - 40, h - 40]
                ], dtype="float32")
            
            # Perspektif matrisini hesapla ve düzeltmeyi uygula
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(frame, M, (w, h))
            cv2.imshow("Keystone Corrected View", warped)
        else:
            cv2.imshow("Projector Keystone Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
