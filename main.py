import cv2
import numpy as np
import time

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

def detect_advanced_markers(frame):
    """
    Köşelerdeki ve merkezdeki kalibrasyon işaretlerini tespit eder.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Yeşil renk aralığı (kalibrasyon işaretleri için)
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    points = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 8 < area < 1500:  # Çok küçük gürültüleri ve devasa lekeleri ele
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                points.append((cX, cY))
                
    if len(points) >= 4:
        # En dıştaki 4 köşeyi seçmek için numpy sıralaması
        points = np.array(points, dtype="float32")
        s = points.sum(axis=1)
        rect = np.zeros((4, 2), dtype="float32")
        rect[0] = points[np.argmin(s)]     # Sol-üst
        rect[3] = points[np.argmax(s)]     # Sağ-alt
        
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]    # Sağ-üst
        rect[2] = points[np.argmax(diff)]    # Sol-alt
        return rect
        
    return None

def draw_notification(frame, message):
    """
    Ekranın alt veya üst kısmında şık, şeffaf arka planlı bir bildirim bandı çizer.
    """
    h, w, _ = frame.shape
    overlay = frame.copy()
    # Alt kısımda siyah bir bildirim şeridi
    cv2.rectangle(overlay, (0, h - 50), (w, h), (0, 0, 0), -1)
    alpha = 0.6
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    cv2.putText(frame, message, (20, h - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

def main():
    print("Searching for available camera devices...")
    cam_index = find_working_camera()
    
    if cam_index is None:
        print("NOTIFICATION: Camera could not be detected!")
        return

    print(f"Camera successfully found at index: {cam_index}")
    cap = cv2.VideoCapture(cam_index)

    # Optimizasyon ve Durum Değişkenleri
    is_calibrated = False
    calibration_active_frames = 0
    blocked_counter = 0
    prev_gray = None
    cached_matrix = None
    
    # Grid/Geometrik Desen aralığı ve sayaçları
    trigger_cooldown = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # 1. HATA KONTROLÜ: Kamera engellenmiş mi veya ortam tamamen karanlık mı?
        avg_brightness = np.mean(gray)
        if avg_brightness < 12:  # Çok karanlık / Film izleniyor veya önü kapalı
            blocked_counter += 1
            if blocked_counter > 30:
                draw_notification(frame, "UYARI: Kamera kapali veya ekran algilanamiyor! Onunu acin.")
                cv2.imshow("Projector Keystone Auto-System", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
        else:
            blocked_counter = 0

        # 2. HAREKET VE AÇI DEĞİŞİKLİĞİ TESPİTİ (İşlemciyi yormayan hafif fark algoritması)
        motion_detected = False
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            non_zero_count = np.count_nonzero(diff > 30)
            # Eğer piksellerin %3'ünden fazlasında ani değişim varsa (fiziksel sarsıntı / açı değişimi)
            if non_zero_count > (w * h * 0.03):
                motion_detected = True
                calibration_active_frames = 45  # 45 kare boyunca kalibrasyon modunda kal
        
        prev_gray = gray.copy()

        # Eğer tetiklenmişse veya ilk açılışsa kalibrasyon sürecini başlat
        if not is_calibrated or motion_detected or calibration_active_frames > 0:
            # İşleme etki etmeyecek şekilde köşelere, kenarlara ve ortaya akıllı referans şekilleri koy
            cv2.circle(frame, (50, 50), 8, (0, 255, 0), -1)          # Sol-üst
            cv2.circle(frame, (w - 50, 50), 8, (0, 255, 0), -1)     # Sağ-üst
            cv2.circle(frame, (50, h - 50), 8, (0, 255, 0), -1)     # Sol-alt
            cv2.circle(frame, (w - 50, h - 50), 8, (0, 255, 0), -1) # Sağ-alt
            cv2.circle(frame, (w // 2, h // 2), 6, (255, 0, 0), -1) # Merkez referansı
            
            # Hafif bir grid pattern (test amaçlı kılavuz çizgiler)
            cv2.line(frame, (50, 50), (w - 50, 50), (0, 255, 0, 100), 1)
            cv2.line(frame, (50, h - 50), (w - 50, h - 50), (0, 255, 0, 100), 1)

            # Otomatik köşe tespiti dene
            src_pts = detect_advanced_markers(frame)
            if src_pts is not None:
                dst_pts = np.array([
                    [50, 50],
                    [w - 50, 50],
                    [50, h - 50],
                    [w - 50, h - 50]
                ], dtype="float32")
                
                cached_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                is_calibrated = True

            if calibration_active_frames > 0:
                calibration_active_frames -= 1

        # 3. KESTİRİM / KEYSTONE UYGULAMA (Cachelenmiş matris varsa işlemciyi yormadan direkt uygula)
        if is_calibrated and cached_matrix is not None:
            corrected_frame = cv2.warpPerspective(frame, cached_matrix, (w, h))
            cv2.imshow("Projector Keystone Auto-System", corrected_frame)
        else:
            # Henüz kalibre olamadıysa veya ekran algılanamıyorsa normal çerçeveyi ve uyarıyı göster
            if not is_calibrated:
                draw_notification(frame, "BILGI: Ekran kalibre ediliyor, lutfen bekleyin...")
            cv2.imshow("Projector Keystone Auto-System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
