import logging
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, WebSocket, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2
import numpy as np
import shutil
import os
import io
import time
import json
import asyncio

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("backend.log")
    ]
)
logger = logging.getLogger(__name__)

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

app = FastAPI(
    title="ID Card Detection API",
    description="Backend API for real-time ID card compliance monitoring and video analysis.",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve violation images as static files
from fastapi.staticfiles import StaticFiles
violations_dir = "database/violations"
if not os.path.exists(violations_dir):
    os.makedirs(violations_dir)
app.mount("/violations", StaticFiles(directory=violations_dir), name="violations")


# Global Variables
face_ident = None
tracker = None
model = None
TOTAL_DETECTIONS = 0

@app.on_event("startup")
async def startup_event():
    global face_ident, tracker, model
    try:
        logger.info("Initializing system...")
        create_db_and_tables()
        
        logger.info("Loading YOLO model...")
        model = YOLO("idcard.pt")
        
        logger.info("Initializing Face Identifier and Tracker...")
        face_ident = FaceIdentifier()
        tracker = ComplianceTracker(face_ident) 
        
        logger.info("System startup complete.")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise RuntimeError(f"Startup failed: {e}")

# --- Authentication Endpoints ---

@app.post("/token", tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", tags=["Authentication"])
async def register_user(user_data: User, session: Session = Depends(get_session)):
    statement = select(User).where(User.username == user_data.username)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    user_data.hashed_password = get_password_hash(user_data.hashed_password)
    session.add(user_data)
    session.commit()
    session.refresh(user_data)
    logger.info(f"New user registered: {user_data.username}")
    return {"message": "User registered successfully"}

# --- Protected Endpoints ---

@app.get("/users/me", tags=["User"], response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/", tags=["General"])
def read_root():
    return {"status": "Online", "service": "ID Card Detection API", "version": "3.0.0"}

@app.get("/stats", tags=["Monitoring"])
async def get_stats(session: Session = Depends(get_session)):
    global TOTAL_DETECTIONS
    
    try:
        statement = select(ViolationLog)
        results = session.exec(statement).all()
        violation_count = len(results)
        
        rate = 100.0
        if TOTAL_DETECTIONS > 0:
            rate = ((float(TOTAL_DETECTIONS) - float(violation_count)) / float(TOTAL_DETECTIONS)) * 100.0
            rate = max(0.0, min(100.0, rate))

        return {
            "total_detections": TOTAL_DETECTIONS,
            "compliance_rate": f"{rate:.1f}%",
            "violations": violation_count,
            "active_cameras": 1,
            "system_status": "healthy"
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {"error": "Failed to fetch stats"}

@app.get("/violations_list", tags=["Monitoring"])
async def get_violations_list(session: Session = Depends(get_session)):
    try:
        statement = select(ViolationLog).order_by(ViolationLog.timestamp.desc())
        violations = session.exec(statement).all()
        
        return [
            {
                "id": v.id,
                "person_name": v.person_name,
                "timestamp": v.timestamp.isoformat(),
                "image_path": v.image_path,
                "track_id": v.track_id,
                "status": v.status
            }
            for v in violations
        ]
    except Exception as e:
        logger.error(f"Error fetching violations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch violations")


@app.post("/detect", tags=["Real-time Detection"])
async def detect_frame(file: UploadFile = File(...)):
    global model, tracker, TOTAL_DETECTIONS
    
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

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
                    TOTAL_DETECTIONS += 1
                elif cls == 0: 
                    id_card_boxes.append(coords)

        display_data = tracker.update(frame, person_tracks, id_card_boxes)

        height, width = frame.shape[:2]
        formatted_results = []
        
        for item in display_data:
            x1, y1, x2, y2 = item['bbox']
            formatted_results.append({
                "bbox": [x1 / width, y1 / height, x2 / width, y2 / height], 
                "status": item['status'],
                "color": item['color'],
                "name": item.get('name', 'Unknown')
            })

        return {
            "detections": formatted_results,
            "person_count": len(person_tracks),
            "id_card_count": len(id_card_boxes)
        }
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail="Detection failed")

@app.post("/analyze_video", tags=["Video Analysis"])
async def analyze_video(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    temp_filename = f"temp_{int(time.time())}_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Video uploaded for analysis: {file.filename}")
    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

    async def video_processor():
        global model, tracker, face_ident
        
        cap = cv2.VideoCapture(temp_filename)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        violations_data = {}
        analyzed_frames = 0
        frame_step = 5 
        
        start_time = time.time()
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                analyzed_frames += 1
                if analyzed_frames % frame_step != 0:
                    continue
                    
                progress = analyzed_frames / total_frames if total_frames > 0 else 0
                
                yield json.dumps({
                    "status": "processing",
                    "progress": round(progress * 100, 1),
                    "frame": analyzed_frames
                }) + "\n"
                
                results = model.track(frame, persist=True, verbose=False, conf=0.4)
                
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
                    
                    display_data = tracker.update(frame, person_tracks, id_card_boxes)
                    
                    for item in display_data:
                        if "VIOLATION" in item['status']:
                            track_id = item['track_id'] if 'track_id' in item else item.get('id', 0)
                            if track_id not in violations_data:
                                person_name = item.get('name', 'Unknown')
                                bbox = item['bbox']
                                if person_name == 'Unknown' or person_name == '':
                                    person_name = face_ident.identify(frame, bbox)
                                
                                from modules.utils import save_violation
                                image_path = save_violation(frame, person_name, bbox)
                                
                                seconds = (analyzed_frames) / fps if fps > 0 else 0
                                violations_data[track_id] = {
                                    "name": person_name,
                                    "timestamp": round(seconds, 2),
                                    "image_path": image_path
                                }
                                violation_log = ViolationLog(
                                    person_name=person_name,
                                    image_path=image_path,
                                    track_id=track_id, 
                                    status="VIOLATION"
                                )
                                session.add(violation_log)
                                session.commit()
                
                await asyncio.sleep(0.001)

        finally:
            cap.release()
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        
        final_response = {
            "status": "complete",
            "total_frames": analyzed_frames,
            "violations_found": len(violations_data),
            "summary": list(violations_data.values())
        }
        yield json.dumps(final_response) + "\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(video_processor(), media_type="application/x-ndjson")


if __name__ == "__main__":
    logger.info("Starting API server...")
    uvicorn.run("server:app", host="0.0.0.0", port=8085, reload=False)
