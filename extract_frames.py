import cv2
import os

def extract_frames(video_paths, output_dir, interval=5):
    """
    Extracts frames from a list of videos at a specified interval.

    Args:
        video_paths (list): List of paths to video files.
        output_dir (str): Directory to save the extracted images.
        interval (int): Save every nth frame.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    total_images_saved = 0

    for video_path in video_paths:
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            continue

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"Error: Could not open video: {video_path}")
            continue

        print(f"Processing video: {video_name}...")
        
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % interval == 0:
                output_filename = f"{video_name}_frame_{frame_count}.jpg"
                output_path = os.path.join(output_dir, output_filename)
                cv2.imwrite(output_path, frame)
                saved_count += 1
                total_images_saved += 1
            
            frame_count += 1

        cap.release()
        print(f"Finished {video_name}. Saved {saved_count} images.")

    print(f"Done! Total images saved: {total_images_saved}")

if __name__ == "__main__":
    # Define video paths
    base_dir = r"c:\Users\vmnit\Desktop\ID Card 3.0"
    videos = [
        "VID20260102131145.mp4",
        "VID20260102131231.mp4",
        "VID20260102131305.mp4"
    ]
    
    video_paths = [os.path.join(base_dir, v) for v in videos]
    output_dir = os.path.join(base_dir, "dataset")

    # Run extraction
    extract_frames(video_paths, output_dir, interval=5)
