"""
Advanced Trash AI – handle single trash & large dump sites
"""

import os
from ultralytics import YOLO
from PIL import Image
import numpy as np

# =========================
# LOAD YOLO
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")
model = YOLO(MODEL_PATH)

# =========================
# YOLO CLASS → TRASH TYPE
# =========================
CLASS_MAP = {
    39: "nhua",        # bottle
    41: "nhua",        # cup
    44: "nhua",
    46: "kim_loai",    # can
}

# =========================
# DETECT OBJECT TRASH
# =========================
def detect_trash_objects(image_path: str):
    trash_types = []
    object_count = 0

    results = model(image_path, conf=0.25)

    for r in results:
        if r.boxes is None:
            continue

        for cls_id in r.boxes.cls.tolist():
            cls_id = int(cls_id)
            if cls_id in CLASS_MAP:
                trash_types.append(CLASS_MAP[cls_id])
                object_count += 1

    return trash_types, object_count

# =========================
# SCENE HEURISTIC (BÃI RÁC LỚN)
# =========================
def analyze_scene(image_path: str):
    """
    Phát hiện bãi rác dựa trên mật độ màu & texture
    """
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)

    # Độ biến thiên màu (nhiều màu hỗn loạn = rác)
    color_variance = np.var(arr)

    # Ngưỡng thực nghiệm
    if color_variance > 2500:
        return True
    return False

# =========================
# ƯỚC TÍNH KHỐI LƯỢNG
# =========================
def estimate_weight(object_count: int, large_dump: bool):
    if large_dump:
        return round(2.5 + object_count * 0.02, 2)  # bãi rác lớn

    return round(object_count * 0.03, 2)  # rác nhỏ lẻ

# =========================
# NHÂN LỰC
# =========================
def recommend_volunteers(weight: float):
    return max(3, int(weight * 8))

# =========================
# MAIN API
# =========================
def analyze_images(image_paths: list[str]) -> dict:
    all_types = []
    total_objects = 0
    large_dump_detected = False

    for path in image_paths:
        if not os.path.exists(path):
            continue

        types, count = detect_trash_objects(path)
        all_types.extend(types)
        total_objects += count

        if analyze_scene(path):
            large_dump_detected = True

    # Nếu là bãi rác lớn → override
    if large_dump_detected:
        weight = estimate_weight(total_objects, True)
        volunteers = recommend_volunteers(weight)

        return {
            "trash_types": ["nhua", "khac"],
            "weight": weight,
            "volunteers": volunteers,
            "summary": (
                "AI phát hiện đây là một bãi rác lớn ngoài trời "
                "với nhiều loại rác hỗn hợp. "
                f"Khối lượng ước tính khoảng {weight} tấn. "
                f"Đề xuất {volunteers} tình nguyện viên."
            ),
        }

    # Trường hợp rác nhỏ lẻ
    if not all_types:
        return {
            "trash_types": [],
            "weight": 0.0,
            "volunteers": 3,
            "summary": "AI không phát hiện được rác rõ ràng trong hình.",
        }

    weight = estimate_weight(total_objects, False)
    volunteers = recommend_volunteers(weight)

    return {
        "trash_types": list(set(all_types)),
        "weight": weight,
        "volunteers": volunteers,
        "summary": (
            f"AI phát hiện {total_objects} vật thể rác. "
            f"Khối lượng ước tính {weight} tấn. "
            f"Đề xuất {volunteers} tình nguyện viên."
        ),
    }
