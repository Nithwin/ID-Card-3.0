import cv2
from ultralytics import YOLO

def main():
    # Load the YOLOv11 model
    # Assuming the user has 'idcard.pt' in the same directory
    model_path = "idcard.pt"
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Error loading model from {model_path}: {e}")
        return

    # Open the webcam (source 0 is usually the default webcam)
    cap = cv2.VideoCapture("test1.mp4")

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        # Run inference on the frame
        # stream=True is efficient for video sources
        results = model(frame, stream=True)

        # Iterate over results and render them on the frame
        for result in results:
            # plot() returns a BGR numpy array of the annotated image
            annotated_frame = result.plot()

            # Display the annotated frame
            cv2.imshow("YOLOv11 Live Inference", annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
