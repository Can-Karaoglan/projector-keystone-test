import cv2
import numpy as np

def find_working_camera():
    # Negatif indeks (-1) ve 0'dan 5'e kadar olan tüm alternatifleri güvenli tarama
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
            cv2.circle(frame, (40, 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (w - 40, 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (40, h - 40), 6, (0, 255, 0), -1)
            cv2.circle(frame, (w - 40, h - 40), 6, (0, 255, 0), -1)
            is_calibrated = True

        cv2.imshow("Projector Keystone Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
