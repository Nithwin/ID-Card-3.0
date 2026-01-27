
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, WebSocket, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2
import numpy as np
import shutil
import os
import io

# Import Modules
from modules.face_ident import FaceIdentifier
from modules.tracker import ComplianceTracker
from ultralytics import YOLO

# Import DB & Auth
from database_config import create_db_and_tables, get_session, Session, User, ViolationLog
from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    create_access_token, 
    get_current_user, 
    verify_password, 
    get_password_hash
)
from sqlmodel import select

app = FastAPI(title="ID Card Compliance API V3")

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
    print("[INFO] Creating Database Tables...")
    create_db_and_tables()
    
    print("[INFO] Loading Models...")
    face_ident = FaceIdentifier()
    tracker = ComplianceTracker(face_ident) 
    model = YOLO("idcard.pt")
    print("[INFO] Models Loaded.")

# --- Authentication Endpoints ---

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register_user(user_data: User, session: Session = Depends(get_session)):
    statement = select(User).where(User.username == user_data.username)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password
    user_data.hashed_password = get_password_hash(user_data.hashed_password)
    session.add(user_data)
    session.commit()
    session.refresh(user_data)
    return {"message": "User registered successfully"}

# --- Protected Endpoints ---

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/")
def read_root():
    return {"status": "Online", "service": "ID Card Compliance v3.0", "port": 8081}

@app.post("/detect")
async def detect_frame(
    file: UploadFile = File(...),
    # current_user: User = Depends(get_current_user) # Uncomment to enforce auth strictly
):
    """
    Receives an image file, runs detection, and returns bounding boxes.
    """
    global model, tracker
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return {"error": "Invalid image"}

    # --- Detection Logic ---
    results = model.track(frame, persist=True, verbose=False, conf=0.4)
    
    person_tracks = []
    id_card_boxes = []

    if results and results[0].boxes:
        for box in results[0].boxes:
            cls = int(box.cls[0])
            coords = box.xyxy[0].cpu().numpy().tolist()
            
            if cls == 1 and box.id is not None: 
                tid = int(box.id[0])
                person_tracks.append(coords + [tid]) 
            elif cls == 0: 
                id_card_boxes.append(coords)

    # --- Tracker Update ---
    display_data = tracker.update(frame, person_tracks, id_card_boxes)

    # Serialize & Normalize
    height, width = frame.shape[:2]
    formatted_results = []
    
    for item in display_data:
        x1, y1, x2, y2 = item['bbox']
        nx1, ny1 = x1 / width, y1 / height
        nx2, ny2 = x2 / width, y2 / height

        formatted_results.append({
            "bbox": [nx1, ny1, nx2, ny2], 
            "status": item['status'],
            "color": item['color'],
            "name": item.get('name', 'Unknown')
        })

    return {
        "detections": formatted_results,
        "person_count": len(person_tracks),
        "id_card_count": len(id_card_boxes)
    }

@app.post("/analyze_video")
async def analyze_video(
    file: UploadFile = File(...),
    # current_user: User = Depends(get_current_user)
):
    """
    Upload a video file, process it frame-by-frame, and return a summary.
    For this MVP, we will process a few frames or sampled frames to be fast.
    """
    global model, tracker
    
    # Save Temp File
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cap = cv2.VideoCapture(temp_filename)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    violation_frames = []
    analyzed_frames = 0
    frame_step = 5 # Process every 5th frame for speed
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            analyzed_frames += 1
            if analyzed_frames % frame_step != 0:
                continue
                
            # Logic similar to detect
            results = model.track(frame, persist=True, verbose=False, conf=0.4)
            
            # Simple check for simple summary
            has_violation = False
            
            if results and results[0].boxes:
                person_tracks = []
                id_card_boxes = []
                for box in results[0].boxes:
                    cls = int(box.cls[0])
                    coords = box.xyxy[0].cpu().numpy().tolist()
                    if cls == 1 and box.id is not None:
                         person_tracks.append(coords + [int(box.id[0])])
                    elif cls == 0:
                         id_card_boxes.append(coords)
                
                # Update Tracker (updates state)
                display_data = tracker.update(frame, person_tracks, id_card_boxes)
                
                # Check for active violations in this frame
                for item in display_data:
                    if "VIOLATION" in item['status']:
                        has_violation = True
            
            if has_violation:
                # Capture timestamp
                seconds = (analyzed_frames * frame_step) / fps if fps > 0 else 0
                violation_frames.append({
                    "frame": analyzed_frames,
                    "seconds": round(seconds, 2),
                    "violation": "No ID Card"
                })

    finally:
        cap.release()
        os.remove(temp_filename)

    return {
        "filename": file.filename,
        "total_frames_processed": analyzed_frames,
        "violations_detected": len(violation_frames),
        "violation_timestamps": violation_frames
    }

if __name__ == "__main__":
    # Force 8081 to avoid permissions issues
    print("Running on http://127.0.0.1:8081")
    uvicorn.run("server:app", host="0.0.0.0", port=8081, reload=False)
