import numpy as np
from .utils import save_violation

class ComplianceTracker:
    def __init__(self, face_identifier):
        self.face_identifier = face_identifier
        
        # State: {track_id: {'no_id_frames': 0, 'logged': False, 'name': None}}
        self.people_state = {} 
        self.VIOLATION_THRESHOLD = 25

    def update(self, frame, person_tracks, id_card_boxes):
        """
        person_tracks: List of [x1, y1, x2, y2, track_id, conf, cls] (from YOLO track)
        id_card_boxes: List of [x1, y1, x2, y2]
        """
        # Create a set of current track_ids for cleanup
        current_track_ids = set()
        
        results_to_display = []

        for track in person_tracks:
            # Unpack track info (Ultralytics format usually: x1, y1, x2, y2, id, ...)
            # Check length to be safe
            if len(track) < 5:
                continue
                
            x1, y1, x2, y2 = track[:4]
            track_id = int(track[4])
            current_track_ids.add(track_id)

            # Initialize state if new
            if track_id not in self.people_state:
                self.people_state[track_id] = {'no_id_frames': 0, 'logged': False, 'name': 'Unknown'}

            # Check for ID Card association
            has_id = False
            person_box = [x1, y1, x2, y2]
            
            for id_box in id_card_boxes:
                if self.check_overlap(person_box, id_box):
                    has_id = True
                    break

            # Update Counters
            state = self.people_state[track_id]
            
            if has_id:
                state['no_id_frames'] = 0  # Reset if ID is seen
                status = "COMPLIANT"
                color = (0, 255, 0)
            else:
                state['no_id_frames'] += 1
                status = f"CHECKING {state['no_id_frames']}/{self.VIOLATION_THRESHOLD}"
                color = (0, 255, 255) # Yellow

            # Check Violation Trigger
            if state['no_id_frames'] >= self.VIOLATION_THRESHOLD and not state['logged']:
                # VIOLATION CONFIRMED
                status = "VIOLATION"
                color = (0, 0, 255) # Red
                
                # Identify Person
                name = self.face_identifier.identify(frame, person_box)
                state['name'] = name
                
                # Capture and Save (Blur Logic)
                # The user wants to: "blur the other than the person who doesn't wear the id card"
                # My `save_violation` does exactly this: blurs background/others, keeps subject clear.
                save_violation(frame, name, person_box)
                
                state['logged'] = True
            
            elif state['logged']:
                 # Already logged, just show status
                 status = f"LOGGED: {state['name']}"
                 color = (0, 0, 255)

            results_to_display.append({
                'bbox': person_box,
                'id': track_id,
                'status': status,
                'color': color,
                'name': state['name'] if state['logged'] else ""
            })

        # clean up old tracks (optional, simple version just keeps growing for now or we remove missing)
        # self.cleanup_states(current_track_ids)
        
        return results_to_display

    def check_overlap(self, person_box, id_box):
        """
        Check if ID card is substantially inside the person box.
        """
        px1, py1, px2, py2 = person_box
        ix1, iy1, ix2, iy2 = id_box
        
        # Calculate ID card center
        icx = (ix1 + ix2) / 2
        icy = (iy1 + iy2) / 2
        
        # Check if center of ID card is inside person bbox
        if px1 < icx < px2 and py1 < icy < py2:
            return True
        return False
