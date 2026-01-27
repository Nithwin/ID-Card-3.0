
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2
import numpy as np
import shutil
import os
import io

# Import existing logic (adjusted for new structure)
from modules.face_ident import FaceIdentifier
from modules.tracker import ComplianceTracker
from ultralytics import YOLO

app = FastAPI(title="ID Card Compliance API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Variables
face_ident = None
tracker = None
model = None

@app.on_event("startup")
async def startup_event():
    global face_ident, tracker, model
    print("[INFO] Loading Models...")
    # Initialize Models
    face_ident = FaceIdentifier()
    # Note: ComplianceTracker expects face_ident
    tracker = ComplianceTracker(face_ident) 
    model = YOLO("idcard.pt")
    print("[INFO] Models Loaded.")

@app.get("/")
def read_root():
    return {"status": "Online", "service": "ID Card Compliance v3.0"}

@app.post("/detect")
async def detect_frame(file: UploadFile = File(...)):
    """
    Receives an image file, runs detection, and returns:
    - Bounding Boxes
    - Compliance Status
    - Processed Image (optional, or just coordinates)
    """
    global model, tracker
    
    # Read Image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return {"error": "Invalid image"}

    # --- Detection Logic (Reused from main_app_v2) ---
    # Resize for speed if needed (optional)
    # ...

    results = model.track(frame, persist=True, verbose=False, conf=0.4)
    
    person_tracks = []
    id_card_boxes = []

    if results and results[0].boxes:
        for box in results[0].boxes:
            cls = int(box.cls[0])
            coords = box.xyxy[0].cpu().numpy().tolist()
            
            if cls == 1 and box.id is not None: 
                tid = int(box.id[0])
                person_tracks.append(coords + [tid]) # [x1, y1, x2, y2, tid]
            elif cls == 0: 
                id_card_boxes.append(coords) # [x1, y1, x2, y2]

    # --- Tracker Update ---
    display_data = tracker.update(frame, person_tracks, id_card_boxes)

    # Serialize display_data for JSON response
    # Normalize coordinates for easier frontend display
    height, width = frame.shape[:2]
    
    formatted_results = []
    for item in display_data:
        x1, y1, x2, y2 = item['bbox']
        
        # Normalize (0.0 - 1.0)
        nx1, ny1 = x1 / width, y1 / height
        nx2, ny2 = x2 / width, y2 / height

        formatted_results.append({
            "bbox": [nx1, ny1, nx2, ny2], 
            "status": item['status'],
            "color": item['color'],
            "velocity": item.get('velocity', 0),
            "track_id": item.get('track_id', -1),
            "name": item.get('name', 'Unknown')
        })

    return {
        "detections": formatted_results,
        "person_count": len(person_tracks),
        "id_card_count": len(id_card_boxes)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
