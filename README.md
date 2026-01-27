
# ID Card 3.0 Compliance System

## Overview
This project is an AI-powered surveillance system designed to detect and track individuals in real-time, verifying if they are wearing an ID card. It uses **YOLOv8** for object detection and **InsightFace** for face recognition.

## Features
- **Real-time Detection**: Identifies Persons and ID Cards.
- **Compliance Tracking**: Tracks individuals and flags them if they are not wearing an ID card for a certain duration.
- **Identity Verification**: Uses facial recognition to log the identity of specific violators.
- **Behavioral Analysis**: Tracks movement velocity and trajectory.

## Prerequisites
- Python 3.9+
- CUDA-capable GPU (Recommended for real-time performance)

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the main application:
```bash
python main_app_v2.py
```

## Project Structure
- `main_app_v2.py`: Main application entry point (GUI & Logic).
- `modules/`: Helper modules for Face Identification (`face_ident.py`) and Tracking (`tracker.py`).
- `database/`: Stores face embeddings for recognition.
- `dataset/`: Training data (if applicable).
- `idcard.pt`: YOLOv8 model trained for ID Card detection.
