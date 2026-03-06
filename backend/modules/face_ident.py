import cv2
import os
import pickle
import numpy as np

try:
    import insightface
    from insightface.app import FaceAnalysis
    HAS_INSIGHTFACE = True
except ImportError:
    HAS_INSIGHTFACE = False
    print("[WARNING] insightface not found. Using simple OpenCV fallback for face detection.")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    def cosine_similarity(a, b):
        # Fallback simple cosine similarity using numpy
        norm_a = np.linalg.norm(a, axis=1, keepdims=True)
        norm_b = np.linalg.norm(b, axis=1, keepdims=True)
        return np.dot(a, b.T) / (norm_a * norm_b.T)

class FaceIdentifier:
    def __init__(self, db_path="database/known_faces", encodings_path="database/encodings.pkl"):
        self.db_path = db_path
        self.encodings_path = encodings_path
        self.known_face_embeddings = []
        self.known_face_names = []
        
        if HAS_INSIGHTFACE:
            try:
                self.app = FaceAnalysis(name='buffalo_l') 
                self.app.prepare(ctx_id=0, det_size=(640, 640)) 
                self.load_encodings()
            except Exception as e:
                print(f"[ERROR] Failed to init InsightFace: {e}. Falling back to OpenCV.")
                self.setup_fallback()
        else:
            self.setup_fallback()

    def setup_fallback(self):
        self.has_ai = False
        # Load a simple Haar Cascade for detection only
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        print("[INFO] OpenCV Face Cascade loaded as fallback.")

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
        if not HAS_INSIGHTFACE:
            print("[WARNING] Cannot build encodings without InsightFace.")
            return

        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            return

        image_files = [f for f in os.listdir(self.db_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        embeddings_list = []
        names_list = []

        for filename in image_files:
            name = os.path.splitext(filename)[0]
            img_path = os.path.join(self.db_path, filename)
            img = cv2.imread(img_path)
            if img is None: continue

            faces = self.app.get(img)
            if len(faces) > 0:
                embedding = faces[0].embedding
                embeddings_list.append(embedding)
                names_list.append(name)
            else:
                print(f"[WARNING] No face found in {filename}")

        if embeddings_list:
            self.known_face_embeddings = np.array(embeddings_list)
            self.known_face_names = names_list
            data = {"embeddings": self.known_face_embeddings, "names": self.known_face_names}
            with open(self.encodings_path, 'wb') as f:
                pickle.dump(data, f)
            print("[INFO] Embeddings saved.")

    def identify(self, frame, person_bbox, threshold=0.35):
        """Identifies the person within the bbox."""
        x1, y1, x2, y2 = map(int, person_bbox)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        person_roi = frame[y1:y2, x1:x2]
        if person_roi.size == 0:
            return "Unknown"

        if HAS_INSIGHTFACE and len(self.known_face_embeddings) > 0:
            try:
                faces = self.app.get(frame)
                if not faces:
                    faces = self.app.get(person_roi)
                
                if faces:
                    valid_faces = []
                    for face in faces:
                        fx1, fy1, fx2, fy2 = face.bbox
                        face_cx = (fx1 + fx2) / 2
                        face_cy = (fy1 + fy2) / 2
                        if x1 <= face_cx <= x2 and y1 <= face_cy <= y2:
                            valid_faces.append(face)
                    
                    if valid_faces:
                        target_face = max(valid_faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
                        target_embedding = target_face.embedding
                        sims = cosine_similarity([target_embedding], self.known_face_embeddings)[0]
                        best_idx = np.argmax(sims)
                        if sims[best_idx] > threshold:
                            return self.known_face_names[best_idx]
            except Exception as e:
                print(f"[ERROR] AI identification failed: {e}")

        # Fallback to simple detection (just to see if a face exists in the box)
        if hasattr(self, 'face_cascade'):
            gray = cv2.cvtColor(person_roi, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                return "Unknown (Face Detected)"
        
        return "Unknown"
