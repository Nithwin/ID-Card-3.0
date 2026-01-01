import cv2
from ultralytics import YOLO
from modules.face_ident import FaceIdentifier
from modules.tracker import ComplianceTracker
import time
import numpy as np

def main():
    print("[INFO] Initializing Face Identity Database...")
    try:
        face_ident = FaceIdentifier()
    except Exception as e:
        print(f"[ERROR] Failed to initialize FaceIdentifier: {e}")
        return

    print("[INFO] Initializing Tracker...")
    tracker = ComplianceTracker(face_ident)

    print("[INFO] Loading YOLO Model...")
    try:
        model = YOLO("best.pt")
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        return

    print("[INFO] Opening Camera...")
    cap = cv2.VideoCapture("test2.mp4")
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    print("[INFO] Starting Live Surveillance... Press 'q' to exit.")

    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to read frame.")
                break

            # Resize frame for performance optimization
            target_width = 1024
            h, w = frame.shape[:2]
            if w > target_width:
                scale = target_width / w
                new_h = int(h * scale)
                frame = cv2.resize(frame, (target_width, new_h))

            # Run Tracking
            results = model.track(frame, persist=True, verbose=False, conf=0.4)
            
            person_tracks = []
            id_card_boxes = []

            if results and results[0].boxes:
                boxes = results[0].boxes
                
                for box in boxes:
                    cls = int(box.cls[0])
                    coords = box.xyxy[0].cpu().numpy()
                    
                    if cls == 1: # Person
                        # Check track ID existence
                        if box.id is not None:
                            track_id = int(box.id[0])
                            person_tracks.append(list(coords) + [track_id])
                        else:
                            # Handling detections without track IDs (rare with .track)
                            pass
                    
                    elif cls == 0: # ID Card
                        id_card_boxes.append(coords)

            # Update Logic
            display_data = tracker.update(frame, person_tracks, id_card_boxes)

            # Draw Results
            for item in display_data:
                x1, y1, x2, y2 = map(int, item['bbox'])
                color = item['color']
                label = item['status']
                if item['name']:
                    label += f" | {item['name']}"

                # Ensure coordinates are valid
                h, w = frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x1, y1 - 25), (x1 + tw, y1), color, -1)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow("ID Card Compliance System", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] Exiting...")
                break
                
        except Exception as e:
            print(f"[ERROR] Loop Exception: {e}")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
