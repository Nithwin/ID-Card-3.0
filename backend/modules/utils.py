import cv2
import numpy as np
import os
from datetime import datetime

def blur_background(frame, focus_bbox):
    """
    Blurs the entire frame except for the region defined by focus_bbox (x1, y1, x2, y2).
    """
    if focus_bbox is None:
        return cv2.GaussianBlur(frame, (21, 21), 0)

    x1, y1, x2, y2 = map(int, focus_bbox)
    h, w = frame.shape[:2]

    # Add padding (e.g., 20% of width/height)
    pad_w = int((x2 - x1) * 0.2)
    pad_h = int((y2 - y1) * 0.2)

    x1 = max(0, x1 - pad_w)
    y1 = max(0, y1 - pad_h)
    x2 = min(w, x2 + pad_w)
    y2 = min(h, y2 + pad_h)
    
    # Global blur
    blurred_frame = cv2.GaussianBlur(frame, (99, 99), 30)
    
    # Copy the clear person (with padding) from original frame
    blurred_frame[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
    
    return blurred_frame

def save_violation(frame, person_name, bbox, violations_dir="database/violations"):
    """
    Saves the processed frame (blurred background) to the violations directory.
    Returns the filepath.
    """
    if not os.path.exists(violations_dir):
        os.makedirs(violations_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{person_name}_{timestamp}.jpg"
    filepath = os.path.join(violations_dir, filename)

    # Process frame: blur everything except the violator
    processed_frame = blur_background(frame, bbox)
    
    cv2.imwrite(filepath, processed_frame)
    print(f"[LOG] Violation saved: {filepath}")
    return filepath
