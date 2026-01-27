# Technical Architecture & Model Workflow

## 1. The Core AI Pipeline
The backend is powered by **3 key AI components** working in sequence for every frame:

### A. Object Detection (YOLOv8)
*   **What it does**: Scans the image to find objects.
*   **Model**: `yolov8n.pt` (Nano version) or custom trained `idcard.pt`.
*   **Target Classes**:
    *   `Person` (Class ID 1)
    *   `ID Card` (Class ID 0)
*   **Output**: Returns "Bounding Boxes" (coordinates `x1, y1, x2, y2`) for every person and ID card found.

### B. ID Card Compliance Logic (Geometry)
*   **What it does**: Connects ID cards to People.
*   **Algorithm**:
    1.  For each `Person` detected, we check if there is an `ID Card` bounding box that overlaps with them or is inside their box.
    2.  **Intersection over Union (IoU)** or simple coordinate containment is used.
*   **Result**:
    *   **COMPLIANT**: Person has an overlapping ID Card.
    *   **VIOLATION**: Person has NO ID Card near them.

### C. Face Recognition (InsightFace)
*   **What it does**: Identifies *who* the person is.
*   **Model**: `buffalo_l` (InsightFace's high-accuracy model).
*   **Workflow**:
    1.  **Face Detection**: Finds the face landmarks within the `Person` box.
    2.  **Embedding Extraction**: Converts the face features into a long list of numbers (a vector/embedding).
    3.  **Vector Search**: Compares this new vector against our database of known vectors (`database/encodings.pkl`) using **Cosine Similarity**.
    4.  **Threshold**: If the similarity score is > 0.4 (40% match), we confirm the identity.
*   **Output**: Returns the Name (e.g., "Admin", "John Doe") to be displayed on the Frontend.

---

## 2. Frontend-Backend Communication
The Flutter app does **not** run the AI. It acts as a "Client":

1.  **Capture**: Flutter Camera takes a picture every 500ms.
2.  **Send**: Sends the image to `http://127.0.0.1:8081/detect` via POST request.
3.  **Process**: Python API receives image -> Runs AI Pipeline -> Returns JSON.
4.  **Display**: Flutter receives JSON -> Draws Bounding Boxes, Status (Violation/Compliant), and Names.

## 3. Tech Stack Details
*   **Backend**: 
    *   **FastAPI**: Fast, async Python web server.
    *   **OpenCV**: Image manipulation.
    *   **SQLModel**: Database interaction (SQLite).
*   **Frontend**:
    *   **Flutter**: Cross-platform UI.
    *   **Dio**: High-performance HTTP client.
    *   **CustomPainter**: Draws the boxes on the screen efficiently.

## 4. Resetting Data
Currently, stats are transient (in-memory) or hardcoded for the demo. To make them persistent and reset-able, we would connect the `home_content.dart` to the `SQLite` database managed by `server.py`.
