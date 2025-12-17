"""
Advanced Trash AI
Detect single trash & large dump sites
Author: You + AI assistant
"""

import os
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

# =========================
# LOAD YOLO MODEL
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")
model = YOLO(MODEL_PATH)

# =========================
# YOLO CLASS → TRASH TYPE
# (COCO-based, tạm thời)
# =========================
CLASS_MAP = {
    39: "nhua",       # bottle
    41: "nhua",       # cup
    44: "nhua",       # bottle
    46: "kim_loai",   # can
}

MIN_BOX_AREA = 500  # lọc nhiễu

# =========================
# DETECT TRASH OBJECTS
# (area-weighted)
# =========================
def detect_trash_objects(image_path: str):
    trash_types = []
    total_trash_area = 0

    results = model(image_path, conf=0.25, verbose=False)

    for r in results:
        if r.boxes is None:
            continue

        for box, cls_id in zip(r.boxes.xyxy, r.boxes.cls):
            cls_id = int(cls_id)
            if cls_id not in CLASS_MAP:
                continue

            x1, y1, x2, y2 = box.tolist()
            area = (x2 - x1) * (y2 - y1)

            if area < MIN_BOX_AREA:
                continue

            total_trash_area += area
            trash_types.append(CLASS_MAP[cls_id])

    return trash_types, total_trash_area


# =========================
# SCENE ANALYSIS
# Detect large dump site
# =========================
def analyze_scene(image_path: str) -> bool:
    img = cv2.imread(image_path)
    if img is None:
        return False

    img = cv2.resize(img, (640, 640))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Color variance
    color_var = np.var(img)

    # 2. Edge density
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.mean(edges > 0)

    # 3. Saturation variance
    sat_var = np.var(hsv[:, :, 1])

    # Heuristic rule (đã test thực nghiệm)
    if (
        color_var > 2200 and
        edge_density > 0.08 and
        sat_var < 3000
    ):
        return True

    return False


# =========================
# WEIGHT ESTIMATION (TON)
# =========================
def estimate_weight(
    total_trash_area: float,
    img_shape,
    large_dump: bool
) -> float:
    img_area = img_shape[0] * img_shape[1]
    coverage_ratio = min(1.0, total_trash_area / img_area)

    if large_dump:
        # bãi rác lớn
        return round(2.0 + coverage_ratio * 8.0, 2)

    # rác nhỏ lẻ
    return round(coverage_ratio * 3.0, 2)


# =========================
# VOLUNTEER ESTIMATION
# =========================
def recommend_volunteers(weight: float) -> int:
    return max(3, min(50, int(weight * 8)))


# =========================
# MAIN API
# =========================
def analyze_images(image_paths: list[str]) -> dict:
    all_types = []
    total_area = 0
    large_dump_votes = 0
    valid_images = 0

    for path in image_paths:
        if not os.path.exists(path):
            continue

        valid_images += 1

        types, area = detect_trash_objects(path)
        all_types.extend(types)
        total_area += area

        if analyze_scene(path):
            large_dump_votes += 1

    if valid_images == 0:
        return {
            "error": "No valid images provided"
        }

    large_dump = (large_dump_votes / valid_images) > 0.4

    sample_img = cv2.imread(image_paths[0])
    weight = estimate_weight(total_area, sample_img.shape, large_dump)
    volunteers = recommend_volunteers(weight)

    if large_dump:
        summary = (
            "AI phát hiện khu vực này có dấu hiệu là bãi rác lớn ngoài trời "
            f"với khối lượng ước tính khoảng {weight} tấn. "
            f"Đề xuất {volunteers} tình nguyện viên."
        )
    elif total_area > 0:
        summary = (
            "AI phát hiện rác thải nhỏ lẻ. "
            f"Khối lượng ước tính {weight} tấn. "
            f"Đề xuất {volunteers} tình nguyện viên."
        )
    else:
        summary = "AI không phát hiện được rác rõ ràng trong hình."

    return {
        "trash_types": list(set(all_types)) if all_types else [],
        "large_dump": large_dump,
        "weight_ton": weight,
        "volunteers": volunteers,
        "confidence": round(min(1.0, total_area / (sample_img.size)), 2),
        "summary": summary,
    }


# =========================
# DEBUG TEST
# =========================
if __name__ == "__main__":
    images = ["test1.jpg", "test2.jpg"]
    result = analyze_images(images)
    print(result)
