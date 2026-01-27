
from ultralytics import YOLO

def export_model():
    print("Loading YOLO model...")
    model = YOLO("idcard.pt")
    print("Exporting to ONNX...")
    model.export(format="onnx", dynamic=False)
    print("Export Complete: idcard.onnx")

if __name__ == "__main__":
    export_model()
