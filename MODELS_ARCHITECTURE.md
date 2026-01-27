# System Architecture & AI Model Documentation

## 1. Project Overview
**ID Card 3.0** is a compliance monitoring system that uses Computer Vision to detect individuals and verify if they are wearing ID cards in real-time or from video footage. The system consists of a **FastAPI** backend and a **Flutter** frontend.

## 2. AI Models Used

### A. Object Detection: YOLOv8 (You Only Look Once)
*   **Model:** `idcard.pt` (Custom trained YOLOv8 model)
*   **Purpose:** To detect two main classes of objects:
    1.  **Persons** (Class 1)
    2.  **ID Cards** (Class 0)
*   **Why YOLOv8?**
    *   **Speed:** YOLOv8 is state-of-the-art for real-time object detection, offering an excellent balance between speed and accuracy (mAP).
    *   **Efficiency:** It can run efficiently on CPUs, which is crucial for local deployment without dedicated GPUs.
    *   **Robustness:** Handles varying lighting conditions and angles better than older generations.

### B. Face Recognition: InsightFace (Buffalo_L)
*   **Library:** `insightface`
*   **Model:** `buffalo_l` (Includes detection, landmark localization, and recognition)
*   **Purpose:** To identify the specific individual who is violating the policy.
*   **Why InsightFace?**
    *   **Accuracy:** One of the most accurate open-source face analysis libraries available.
    *   **Feature-Rich:** distinct models for detection (SCRFD) and recognition (ArcFace) ensure high-quality embeddings even for side profiles.

### C. Object Tracking: ByteTrack
*   **Integration:** Built into YOLOv8 (`model.track`)
*   **Purpose:** To assign unique IDs to detected persons across video frames.
*   **Why ByteTrack?**
    *   **Consistency:** Helps track people even when they are temporarily occluded or the detection flickers.
    *   **Low Overhead:** Extremely fast association algorithm that doesn't significantly slow down the pipeline.

## 3. System Architecture

### Backend (Python/FastAPI)
The backend serves as the brain of the operation.
*   **API Layer:** `FastAPI` handles HTTP requests for video uploads, real-time streams, and data retrieval.
*   **Processing Pipeline:**
    1.  **Ingest:** Receives video frame/file.
    2.  **Detect:** YOLOv8 finds people vs. ID cards.
    3.  **Track:** ByteTrack persists IDs.
    4.  **Logic:** `ComplianceTracker` checks if a "Person" box overlaps with an "ID Card" box.
    5.  **Identify:** If a violation (Person without ID) is found, InsightFace crops the face and matches it against the database.
*   **Database:** SQLite (via SQLModel) stores user accounts, violations, and timestamps.

### Frontend (Flutter)
The frontend provides a cross-platform user interface (Windows/Mobile).
*   **UI Framework:** Flutter for a responsive, glassmorphic design.
*   **State Management:** `setState` (simple) / potential for Riverpod.
*   **Networking:** `Dio` for handling large file uploads and timeouts.

## 4. Optimization Strategies
To ensure the system runs smoothly on standard hardware:
1.  **Frame Skipping:** The video analysis does not process every single frame. It processes every **Nth** frame (e.g., every 5th or 8th frame). This drastically reduces CPU load without missing violations, as human walking speed is slow relative to 30 FPS video.
2.  **On-Demand Recognition:** complex face recognition (expensive) is only triggered *once* per unique track ID when a violation is first confirmed, rather than on every frame.
3.  **Image Resize:** Analysis can be performed on downscaled frames (e.g., 640p) while results are mapped back to original resolution.

## 5. Directory Structure
*   `/backend` - Contains all Python logic, models, and the database.
*   `/frontend` - Contains the Flutter application code.

## 6. Deep Dive: YOLO Architecture

### A. YOLOv5 Architecture
YOLOv5 introduced a streamlined, user-friendly PyTorch implementation that set the standard for speed/accuracy trade-offs.

#### 1. Backbone: CSPDarknet
*   **CSP (Cross Stage Partial) Networks:** The backbone uses CSPDarknet to extract features. CSP modules divide the feature map into two parts: one part goes through a dense block (convolutions), and the other skips it, merging later. This reduces computation while maintaining rich gradient flow.
*   **Focus Layer (Early versions):** Replaced by a 6x6 Conv in later versions, it was used to reduce spatial dimensions initially.
*   **SPPF (Spatial Pyramid Pooling - Fast):** Located at the end of the backbone. It pools features at multiple scales (5x5, 9x9, 13x13) to capture context for objects of different sizes.

#### 2. Neck: PANet (Path Aggregation Network)
*   **FPN + PAN:** Incorporates a Feature Pyramid Network (FPN) and Path Aggregation Network (PANet).
*   **Function:** It aggregates features from different backbone stages (P3, P4, P5).
    *   **Top-down:** Upsamples high-level semantic features to merge with low-level details.
    *   **Bottom-up:** Downsamples low-level features again to pass fine-grained details up to the prediction heads.
*   **C3 Modules:** The neck uses C3 modules (CSP Bottleneck with 3 convolutions) to process these aggregated features.

#### 3. Head: Anchor-Based Detect
*   **Coupled Head:** The classification (what is it?) and localization (where is it?) tasks share some convolutional layers before splitting.
*   **Anchor Boxes:** Relies on predefined "anchor boxes" (reference rectangles) of various aspect ratios. The model predicts offsets from these anchors.
*   **Output:** 3 output layers for detecting small, medium, and large objects.

---

### B. YOLOv8 Architecture (Current State-of-the-Art)
YOLOv8 builds upon v5 but introduces significant structural changes for better accuracy and simplified usage.

#### 1. Backbone: Modified CSPDarknet
*   **C2f Module (Cross-Stage Partial with 2 Flow):** Replaces the **C3** module from v5.
    *   **Difference:** C2f combines the concepts of C3 and ELAN (Efficient Layer Aggregation Network). It has more skip connections (gradient flow paths) than C3, allowing for richer feature representation with similar computational cost.
*   **Conv 3x3:** Replaces the Focus layer (from v5) with a standard 3x3 convolution for downsampling stem.

#### 2. Neck: PANet with C2f
*   Similar structure to v5 (Top-down + Bottom-up) but replaces all **C3** modules with **C2f** modules.
*   Removes the 1x1 convolution before the upsampling stage, streamlining the feature fusion process.

#### 3. Head: Anchor-Free & Decoupled
*   **Decoupled Head:** Unlike v5, the classification and regression (box) branches are completely separate. This allows each branch to focus solely on its specific task without interference.
*   **Anchor-Free:** Removes the need for predefined anchor boxes. It directly predicts the center of an object and the distance to its four boundaries. This generalizes better to irregularly shaped objects and simplifies training.
*   **Loss Functions:**
    *   **VFL (Varifocal Loss):** For classification.
    *   **DFL (Distribution Focal Loss) + CIoU:** For bounding box regression.

### Summary Comparison

| Feature | YOLOv5 | YOLOv8 |
| :--- | :--- | :--- |
| **Backbone Module** | C3 (CSP Bottleneck) | C2f (more skip connections) |
| **Detection Head** | Coupled (Shared layers), Anchor-Based | Decoupled (Separate Class/Box), Anchor-Free |
| **Anchor Boxes** | Requires predefined anchors | **No Anchors** (Direct center prediction) |
| **Loss Function** | Objectness + Class + Box | Task Aligned Assigner (No Objectness branch) |
| **Performance** | Great Speed/Accuracy | **Superior Accuracy** (mAP) for same speed |
