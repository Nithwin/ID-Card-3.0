# ID Card 3.0 Compliance System (V3)

## Overview
**ID Guard 3.0** is an enterprise-grade AI surveillance application designed to ensure ID card compliance in secured areas. It features a **Client-Server architecture** with a high-performance **FastAPI Backend** and a **Modern Flutter Frontend** with a professional "Glassmorphism" UI.

## Features
- **Modern Dashboard**: secure, web-app style dashboard with Sidebar navigation, Glassmorphism, and interactive charts.
- **Authentication**: Secure Login/Registration with JWT & Password Hashing.
- **Real-time Surveillance**: 
    - **YOLOv8** for Person and ID Card detection.
    - **InsightFace** for Identity Recognition.
    - **Compliance Tracking**: Detects if a person is wearing their ID card.
- **Video Analysis**: Upload and analyze pre-recorded video files for violations.
- **Profile Management**: User profile and role management.
- **Persistence**: SQLite database for users and violation logs.

## Architecture & Workflow

### 1. Detection Pipeline (Backend)
The `server.py` handles the core logic:
1.  **Input**: Accepts an image frame (from Live Camera or Video File).
2.  **YOLOv8 (`detect_frame`)**: 
    - Scans the image for `Person` (Class 1) and `ID Card` (Class 0) objects.
    - Returns Bounding Boxes for all detections.
3.  **Compliance Logic (`tracker.py`)**:
    - Checks if an `ID Card` box is spatially **inside** or **near** a `Person` box.
    - If a Person has no associated ID Card -> **VIOLATION**.
    - If a Person has an ID Card -> **COMPLIANT**.
4.  **Identity Recognition (`face_ident.py`)**:
    - If a face is visible, it extracts the face embedding using **InsightFace**.
    - Compares (Cosine Similarity) against a database of known embeddings (`database/encodings.pkl`).
    - Returns the Name of the person or "Unknown".

### 2. Frontend (Flutter)
- **State Management**: Uses `setState` and standard Flutter states (simple & effective).
- **Communication**: Uses `dio` and `http` to send frames to the backend (`POST /detect`).
- **UI Design**: 
    - **Theme**: Deep Slate (`#0F172A`) with Ocean Blue accents.
    - **Components**: Custom `GlassCard`, `ModernSidebar`, and `FlChart` integrations.

## Installation

### Prerequisites
- **Python 3.9+** (Ensure `pip` is upgraded).
- **Flutter SDK** (Latest Stable).
- **C++ Build Tools**: Required for compiling `insightface` or `dlib`. (Visual Studio Build Tools on Windows).

### Backend Setup
1.  Navigate to `backend/`:
    ```powershell
    cd backend
    ```
2.  Install dependencies:
    ```powershell
    pip install fastapi "uvicorn[standard]" sqlmodel python-jose[cryptography] passlib[bcrypt] python-multipart ultralytics insightface onnxruntime opencv-python numpy
    ```
    *Note: If you encounter a `Nuget.exe` error or `insightface` build error, ensure you have C++ Build Tools installed.*

### Frontend Setup
1.  Navigate to `frontend/`:
    ```powershell
    cd frontend
    ```
2.  Install packages:
    ```powershell
    flutter pub get
    ```

## Usage

### 1. Start Support Server
```powershell
cd backend
python server.py
```
*Server runs on: http://127.0.0.1:8081*

### 2. Start Application
```powershell
cd frontend
flutter run -d windows
```

## Troubleshooting
- **Nuget Not Found**: This implies `dlib` or `insightface` is trying to build from source without pre-compiled wheels. Try installing `cmake` (`pip install cmake`) and ensure Visual Studio C++ tools are installed.
- **Port Busy**: Change port 8081 in `server.py` and `api_service.dart`.
- **Model Download**: On first run, YOLO and InsightFace will download models (~200MB). Ensure internet access.
