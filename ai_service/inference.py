"""
추론 담당 — 영상 → 1140개 특성 → (main.py에서) 랜덤포레스트 예측

학습 때와 같은 규칙을 지키는 것이 핵심 (하나라도 다르면 에러 없이 엉뚱한 예측이 나온다)
    - 모든 프레임을 읽고, 프레임마다 확신도가 가장 높은 1명만 사용
    - 관절 좌표: 골반 중심을 (0, 0)으로 옮기고 어깨 폭으로 나눔 → 34개
    - 관절 각도: 왼·오른 팔꿈치, 왼·오른 무릎 (도 단위) → 4개
    - 사람이 잡힌 프레임들을 30스텝으로 리샘플링 → (30, 38) → 한 줄로 펴서 (1, 1140)
"""

import json
from pathlib import Path

import cv2
import joblib
import numpy as np
from ultralytics import YOLO

# ── 모델 불러오기 (함수 밖 = 서버 시작 때 딱 한 번만 실행) ─────────
MODEL_DIR = Path(__file__).parent / "models"

# 학습 설정값 (sequence_steps=30, min_valid_frames=10)을 코드에 또 적지 않고 json에서 읽는다
train_info = json.loads((MODEL_DIR / "rf_training_info.json").read_text(encoding="utf-8"))

pose_model = YOLO(str(MODEL_DIR / "yolo11n-pose.pt"))
rf_model = joblib.load(MODEL_DIR / "rf_action_baseline.joblib")


def frame_feature(xy):
    """관절 17개의 픽셀 좌표 (17, 2) → 특성 38개. 계산할 수 없는 프레임이면 None"""
    # COCO 관절 번호: 어깨 5·6, 팔꿈치 7·8, 손목 9·10, 엉덩이 11·12, 무릎 13·14, 발목 15·16 (왼·오른 순)
    center = (xy[11] + xy[12]) / 2           # 골반 중심 = 두 엉덩이의 가운데
    scale = np.linalg.norm(xy[5] - xy[6])    # 어깨 폭 = 두 어깨 사이 거리
    if scale < 1e-8:                         # 어깨 폭이 0이면 나눌 수 없음
        return None

    # 위치·크기를 맞춘 좌표 34개: [x0, y0, x1, y1, ...] 순서
    feature = list(((xy - center) / scale).reshape(-1))

    # 각도 4개: (a, b, c)에서 b가 꺾이는 관절 → 왼팔꿈치, 오른팔꿈치, 왼무릎, 오른무릎 순서
    for a, b, c in [(5, 7, 9), (6, 8, 10), (11, 13, 15), (12, 14, 16)]:
        ba, bc = xy[a] - xy[b], xy[c] - xy[b]
        len_ba, len_bc = np.linalg.norm(ba), np.linalg.norm(bc)
        if len_ba < 1e-8 or len_bc < 1e-8:   # 두 관절이 같은 점이면 각도를 정할 수 없음
            return None
        cos = np.dot(ba, bc) / (len_ba * len_bc)
        feature.append(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))

    return np.array(feature, dtype=np.float32)


def video_to_input(video_path):
    """영상 → 모델 입력 (1, 1140). 사람이 잡힌 프레임이 부족하면 None"""
    frame_ids, features = [], []

    cap = cv2.VideoCapture(str(video_path))
    try:
        frame_id = 0
        while True:
            ok, frame = cap.read()
            if not ok:                       # 영상 끝
                break

            # imgsz=640, conf=0.25: 학습 데이터를 만들 때 쓴 값
            result = pose_model.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
            if len(result.boxes) > 0:
                best = int(result.boxes.conf.argmax())    # 확신도 1등인 사람
                feature = frame_feature(result.keypoints.xy[best].cpu().numpy())
                if feature is not None:
                    frame_ids.append(frame_id)
                    features.append(feature)
            frame_id += 1
    finally:
        cap.release()                        # 에러가 나도 영상 파일은 닫기

    if len(features) < train_info["min_valid_frames"]:
        return None

    # 30스텝 리샘플링: 프레임 번호를 0~1로 바꾼 뒤, 30개 지점의 값을 앞뒤 프레임 사이에서 보간
    t = (np.array(frame_ids) - frame_ids[0]) / (frame_ids[-1] - frame_ids[0])
    target = np.linspace(0, 1, train_info["sequence_steps"])
    matrix = np.array(features)                                                      # (프레임 수, 38)
    sequence = np.stack([np.interp(target, t, matrix[:, i]) for i in range(38)], axis=1)  # (30, 38)

    # 행 순서로 펴면 t00의 38개 → t01의 38개 → … = rf_feature_columns.json 순서
    return sequence.reshape(1, -1)
