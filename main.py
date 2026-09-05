import cv2
import numpy as np

def main():
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Error: Camera could not be opened.")
        return

    is_calibrated = False
    blocked_counter = 0
    prev_gray = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # 1. Hata Yönetimi: Kamera engellenmiş mi veya karanlık mı kontrolü
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

        # 2. Hareket ve Açı Değişimi Algılama (Motion Trigger)
        motion_detected = False
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            non_zero_count = np.count_nonzero(diff > 25)
            if non_zero_count > (w * h * 0.02):  # Toplam alanın %2'sinden fazla değişim varsa
                motion_detected = True
        prev_gray = gray.copy()

        # 3. Akıllı Kalibrasyon ve Referans Şekilleri
        if not is_calibrated or motion_detected:
            # İzlenen medyaya etki etmeyen köşe referans noktaları (Test için)
            cv2.circle(frame, (40, 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (w - 40, 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (40, h - 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (w - 40, h - 40), 6, (0, 255, 0), -1)
            
            # Gerçek projede cv2.warpPerspective entegrasyonu buraya eklenecektir
            is_calibrated = True

        cv2.imshow("Projector Keystone Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
