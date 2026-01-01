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

    def identify(self, frame, person_bbox, threshold=0.4):
        """
        Identifies the person within the bbox.
        """
        # Crop the person from the frame
        x1, y1, x2, y2 = map(int, person_bbox)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        person_roi = frame[y1:y2, x1:x2]
        if person_roi.size == 0 or self.known_face_embeddings.shape[0] == 0:
            return "Unknown"

        # InsightFace expects full image usually for best detection context, 
        # but running on ROI works if resolution is okay.
        faces = self.app.get(person_roi)

        if not faces:
            return "Unknown"

        # Take the largest face in the ROI
        target_face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
        target_embedding = target_face.embedding

        # Compare with DB
        # Compute Cosine Similarity
        # (A . B) / (||A|| * ||B||) - InsightFace embeddings are usually normalized, 
        # but let's be safe.
        
        sims = cosine_similarity([target_embedding], self.known_face_embeddings)[0]
        
        # Find best match
        best_idx = np.argmax(sims)
        best_score = sims[best_idx]

        if best_score > threshold:
            print(f"[DEBUG] match found: {self.known_face_names[best_idx]} with score {best_score:.2f}")
            return self.known_face_names[best_idx]
        
        print(f"[DEBUG] No match. Best: {self.known_face_names[best_idx]} ({best_score:.2f}) < {threshold}")
        return "Unknown"
