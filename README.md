# ID Card 3.0 Compliance System (V3)

## Overview
A full-stack AI surveillance application designed to ensure ID card compliance in secured areas. 
V3 introduces a Client-Server architecture with a Flutter Frontend and FastAPI Backend.

## Features (V3)
- **Authentication**: Secure Login/Registration with JWT & Password Hashing.
- **Dashboard**: Real-time stats (Compliance Rate, Violations Today) with interactive charts.
- **Live Surveillance**: Real-time camera feed with bounding box overlays for ID Card verification.
- **Video Analysis**: Upload and analyze pre-recorded video files for violations.
- **Modern UI**: "Glassmorphism" Dark Theme built with Flutter.
- **Persistence**: SQLite database for users and violation logs.

## Tech Stack
- **Backend**: Python, FastAPI, SQLModel, SQLite, OpenCV, YOLOv8, InsightFace.
- **Frontend**: Flutter (Windows/Android), Dio, Fl_Chart, Providers.

## Installation

### 1. Prerequisites
- Python 3.9+
- Flutter SDK
- Node.js (optional, for some tools)

### 2. Backend Setup
Navigate to the backend folder:
```powershell
cd backend
```
Install dependencies:
```powershell
pip install fastapi "uvicorn[standard]" sqlmodel python-jose[cryptography] passlib[bcrypt] python-multipart ultralytics insightface onnxruntime opencv-python numpy
```
*Note: If you have a GPU, install `onnxruntime-gpu`. If not, use `onnxruntime`.*

### 3. Frontend Setup
Navigate to the frontend folder:
```powershell
cd frontend
```
Get Flutter packages:
```powershell
flutter pub get
```

## Usage

### Step 1: Start Backend Server
The server must be running for the app to work.
```powershell
cd backend
python server.py
```
*Server runs on: http://127.0.0.1:8081*

### Step 2: Run Flutter App
Open a new terminal and run:
```powershell
cd frontend
flutter run -d windows
```

## How to Use
1.  **Register**: Create a new account on the Login screen.
2.  **Dashboard**: View daily statistics.
3.  **Analyze Video**: Click "Analyze Video File" -> Select a video -> Wait for processing. results will appear below.
4.  **Live Mode**: Click "Start Live Surveillance" to open the camera feed.

## Troubleshooting
- **Port Error**: If Port 8081 is busy, close other python processes or change the port in `server.py` and `frontend/lib/services/api_service.dart`.
- **500 Error**: Ensure `bcrypt` is installed (`pip install bcrypt`).
- **File Picker Error**: Ensure `file_picker` is version `^8.0.0` or `^6.0.0` depending on your Flutter version.
