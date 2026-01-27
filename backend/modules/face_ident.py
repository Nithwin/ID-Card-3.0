import cv2
import os
import pickle
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import cosine_similarity

class FaceIdentifier:
    def __init__(self, db_path="database/known_faces", encodings_path="database/encodings.pkl"):
        self.db_path = db_path
        self.encodings_path = encodings_path
        self.known_face_embeddings = []
        self.known_face_names = []
        
        # Initialize InsightFace
        # providers=['CUDAExecutionProvider'] if gpu else ['CPUExecutionProvider']
        # We'll try to let it auto-detect or default to CPU if GPU fails, but 'onnxruntime-gpu' was requested.
        self.app = FaceAnalysis(name='buffalo_l') 
        self.app.prepare(ctx_id=0, det_size=(640, 640)) 
        
        self.load_encodings()

    def load_encodings(self):
        """Loads face embeddings from pickle or builds them from images."""
        if os.path.exists(self.encodings_path):
            print("[INFO] Loading embeddings from file...")
            with open(self.encodings_path, 'rb') as f:
                data = pickle.load(f)
                self.known_face_embeddings = data["embeddings"]
                self.known_face_names = data["names"]
            print(f"[INFO] Loaded {len(self.known_face_names)} identities.")
        else:
            print("[INFO] No embeddings found. Building from images...")
            self.build_encodings()

    def build_encodings(self):
        """Scans the db_path for images and computes embeddings."""
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            return

        image_files = [f for f in os.listdir(self.db_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # Lists to store
        embeddings_list = []
        names_list = []

        for filename in image_files:
            name = os.path.splitext(filename)[0]
            img_path = os.path.join(self.db_path, filename)
            
            img = cv2.imread(img_path)
            if img is None:
                continue

            faces = self.app.get(img)

            if len(faces) > 0:
                # Assuming one face per reference image is the "main" one.
                # Sort by size just in case, or take the highest detection score.
                # InsightFace returns sorted by det confidence usually.
                embedding = faces[0].embedding
                embeddings_list.append(embedding)
                names_list.append(name)
                print(f"[INFO] Encoded: {name}")
            else:
                print(f"[WARNING] No face found in {filename}")

        self.known_face_embeddings = np.array(embeddings_list)
        self.known_face_names = names_list

        # Save to pickle
        data = {"embeddings": self.known_face_embeddings, "names": self.known_face_names}
        with open(self.encodings_path, 'wb') as f:
            pickle.dump(data, f)
        print("[INFO] Embeddings saved.")

    def identify(self, frame, person_bbox, threshold=0.35):
        """
        Identifies the person within the bbox.
        Lowered threshold to 0.35 for better matching (was 0.4)
        """
        # Crop the person from the frame
        x1, y1, x2, y2 = map(int, person_bbox)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        person_roi = frame[y1:y2, x1:x2]
        if person_roi.size == 0 or len(self.known_face_embeddings) == 0:
            return "Unknown"

        # Use full frame for better detection context, but focus on person region
        # InsightFace works better with full image context
        faces = self.app.get(frame)

        if not faces:
            # Fallback: try ROI if full frame detection fails
            faces = self.app.get(person_roi)
            if not faces:
                return "Unknown"
            # For ROI, just take the largest face
            target_face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
        else:
            # Filter faces that are within the person bbox
            valid_faces = []
            for face in faces:
                fx1, fy1, fx2, fy2 = face.bbox
                # Check if face center is within person bbox
                face_cx = (fx1 + fx2) / 2
                face_cy = (fy1 + fy2) / 2
                if x1 <= face_cx <= x2 and y1 <= face_cy <= y2:
                    valid_faces.append(face)
            
            if not valid_faces:
                return "Unknown"
            
            # Take the largest valid face
            target_face = max(valid_faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
        target_embedding = target_face.embedding

        # Compare with DB - Compute Cosine Similarity
        sims = cosine_similarity([target_embedding], self.known_face_embeddings)[0]
        
        # Find best match
        best_idx = np.argmax(sims)
        best_score = sims[best_idx]
        
        # Debug: show all scores
        print(f"[DEBUG] Face recognition scores:")
        for i, (name, score) in enumerate(zip(self.known_face_names, sims)):
            print(f"  {name}: {score:.3f}")

        if best_score > threshold:
            print(f"[MATCH] Identified: {self.known_face_names[best_idx]} (score: {best_score:.3f}, threshold: {threshold})")
            return self.known_face_names[best_idx]
        
        print(f"[NO MATCH] Best: {self.known_face_names[best_idx]} ({best_score:.3f}) < threshold ({threshold})")
        return "Unknown"
