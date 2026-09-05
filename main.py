import cv2
import numpy as np
import time

def main():
    # Initialize camera (UVC webcam)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Camera could not be opened.")
        return

    # States
    is_calibrated = False
    camera_blocked_counter = 0
    
    print("Starting Keystone Correction Test Loop...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Check if camera view is completely dark or blocked
        avg_brightness = np.mean(gray)
        if avg_brightness < 10:
            camera_blocked_counter += 1
            if camera_blocked_counter > 30:
                # Show notification overlay for blocked/untracked camera
                cv2.putText(frame, "NOTIFICATION: Camera blocked or screen not detected!", 
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.imshow("Projector Keystone Test", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue
        else:
            camera_blocked_counter = 0

        # 2. Initial Calibration with Grid Pattern (Simulated state)
        if not is_calibrated:
            print("Running initial grid pattern calibration...")
            # Placeholder for grid detection logic
            is_calibrated = True
        
        # 3. Trigger-based dynamic check (Movement, Darkness, or Misalignment)
        # If motion or perspective change is detected, display subtle non-intrusive shapes on corners/edges
        
        # Draw placeholder subtle reference markers on corners for testing
        h, w, _ = frame.shape
        cv2.circle(frame, (30, 30), 5, (0, 255, 0), -1)
        cv2.circle(frame, (w - 30, 30), 5, (0, 255, 0), -1)
        cv2.circle(frame, (30, h - 30), 5, (0, 255, 0), -1)
        cv2.circle(frame, (w - 30, h - 30), 5, (0, 255, 0), -1)

        # Show live stream on Termux-X11 display
        cv2.imshow("Projector Keystone Test", frame)

        # Exit loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
