from ultralytics import YOLO

model = YOLO("yolov8n.pt")

results = model("test.jpg", show=True)

print(results)
