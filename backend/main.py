import cv2
import time
import threading
import queue
import numpy as np
from ultralytics import YOLO
from modules.face_ident import FaceIdentifier
from modules.utils import save_violation

# ==========================================
# FEATURE 1: Optimization - Threaded Camera
# ==========================================
# ==========================================
# FEATURE 1: Optimization - Threaded Camera (Fixed)
# ==========================================
class ThreadedCamera:
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src)
        # Fix: Buffer size 1 to prevent lag (always get latest frame)
        self.q = queue.Queue(maxsize=1) 
        self.t = threading.Thread(target=self._reader)
        self.t.daemon = True
        self.stopped = False
        self.t.start()

    def _reader(self):
        while not self.stopped:
            ret, frame = self.capture.read()
            if not ret:
                break
            
            # If full, remove old frame so we can add the new one
            if self.q.full():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            
            self.q.put(frame)

    def read(self):
        try:
            return self.q.get(timeout=1.0) # Wait up to 1s for a frame
        except queue.Empty:
            return None

    def isOpened(self):
        return self.capture.isOpened()

    def release(self):
        self.stopped = True
        self.t.join()
        self.capture.release()

# ==========================================
# FEATURE 2: Unique - Behavioral Tracker V2 (Updated)
# ==========================================
class ComplianceTrackerV2:
    def __init__(self, face_identifier):
        self.face_identifier = face_identifier
        self.people_state = {} 
        self.BASE_THRESHOLD = 25
        self.FAST_MOVER_THRESHOLD = 10 
        self.trails = {} 

    def update(self, frame, person_tracks, id_card_boxes):
        results_to_display = []
        
        active_ids = {t[4] for t in person_tracks}
        self.trails = {k: v for k, v in self.trails.items() if k in active_ids}

        for track in person_tracks:
            x1, y1, x2, y2, track_id = track
            center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)
            
            # --- Update Trails ---
            if track_id not in self.trails:
                self.trails[track_id] = []
            self.trails[track_id].append((center_x, center_y))
            if len(self.trails[track_id]) > 20: 
                self.trails[track_id].pop(0)

            # --- State Init ---
            if track_id not in self.people_state:
                self.people_state[track_id] = {
                    'no_id_frames': 0, 
                    'logged': False, 
                    'name': 'Unknown',
                    'prev_pos': (center_x, center_y),
                    'velocity': 0
                }
            
            state = self.people_state[track_id]
            
            # --- Velocity Calculation ---
            prev_cx, prev_cy = state['prev_pos']
            dist = np.sqrt((center_x - prev_cx)**2 + (center_y - prev_cy)**2)
            state['velocity'] = dist
            state['prev_pos'] = (center_x, center_y)

            threshold = self.FAST_MOVER_THRESHOLD if dist > 25 else self.BASE_THRESHOLD

            # --- ID Association ---
            has_id = False
            person_box = [x1, y1, x2, y2]
            for id_box in id_card_boxes:
                if self.check_overlap(person_box, id_box):
                    has_id = True
                    break

            # --- Status Logic ---
            if has_id:
                state['no_id_frames'] = 0
                status = "COMPLIANT"
                color = (0, 255, 0)
            else:
                state['no_id_frames'] += 1
                
                if state['no_id_frames'] >= threshold:
                    if not state['logged']:
                        name = self.face_identifier.identify(frame, person_box)
                        state['name'] = name
                        save_violation(frame, name, person_box)
                        state['logged'] = True
                    
                    status = f"VIOLATION: {state['name']}"
                    color = (0, 0, 255)
                elif state['logged']:
                    status = f"VIOLATION: {state['name']}"
                    color = (0, 0, 255)
                else:
                    status = f"CHECKING {state['no_id_frames']}/{threshold}"
                    color = (0, 255, 255)

            results_to_display.append({
                'bbox': person_box,
                'status': status,
                'color': color,
                'velocity': dist,
                'track_id': track_id
            })

        return results_to_display

    def check_overlap(self, person_box, id_box):
        px1, py1, px2, py2 = person_box
        ix1, iy1, ix2, iy2 = id_box
        icx, icy = (ix1 + ix2) / 2, (iy1 + iy2) / 2
        return px1 < icx < px2 and py1 < icy < py2

# ==========================================
# Main App V2
# ==========================================
def main():
    print("[INFO] Starting ID Card System V2 (Fixed Lag)...")
    
    try:
        face_ident = FaceIdentifier()
        model = YOLO("idcard.pt")
    except Exception as e:
        print(f"[ERROR] Init failed: {e}")
        return

    tracker = ComplianceTrackerV2(face_ident)
    
    source = "test2.mp4" 
    cap = ThreadedCamera(source)
    time.sleep(1.0) 

    cv2.namedWindow("Surveillance Dashboard", cv2.WINDOW_NORMAL)

    frame_count = 0
    start_time = time.time()

    while True:
        try:
            frame = cap.read()
            if frame is None: 
                # Check if stream ended
                if not cap.isOpened(): 
                    print("[INFO] EOF or Camera Disconnected")
                    break
                # Buffered read might need a moment
                continue

            frame_count += 1
            
            # --- Detection ---
            # Using 640px for speed, but scaling detections back to original
            orig_h, orig_w = frame.shape[:2]
            detect_w = 640
            scale = detect_w / orig_w
            detect_h = int(orig_h * scale)
            
            small_frame = cv2.resize(frame, (detect_w, detect_h))
            results = model.track(small_frame, persist=True, verbose=False, conf=0.4)
            
            person_tracks = []
            id_card_boxes = []

            if results and results[0].boxes:
                for box in results[0].boxes:
                    cls = int(box.cls[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = x1/scale, y1/scale, x2/scale, y2/scale
                    
                    if cls == 1 and box.id is not None: 
                        tid = int(box.id[0])
                        person_tracks.append([x1, y1, x2, y2, tid])
                    elif cls == 0: 
                        id_card_boxes.append([x1, y1, x2, y2])

            # --- Tracker Update ---
            display_data = tracker.update(frame, person_tracks, id_card_boxes)

            # --- Visualization ---
            final_frame = frame 

            # Draw Trails
            for tid, points in tracker.trails.items():
                if len(points) > 1:
                    for i in range(1, len(points)):
                        cv2.line(final_frame, points[i-1], points[i], (0, 165, 255), 2) 

            for item in display_data:
                x1, y1, x2, y2 = map(int, item['bbox'])
                color = item['color']
                
                cv2.rectangle(final_frame, (x1, y1), (x2, y2), color, 2)
                
                label = f"{item['status']} | v:{item['velocity']:.1f}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(final_frame, (x1, y1 - 20), (x1 + tw, y1), color, -1)
                cv2.putText(final_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            fps = frame_count / (time.time() - start_time)
            cv2.putText(final_frame, f"FPS: {fps:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.imshow("Surveillance Dashboard", final_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Loop Error: {e}")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
