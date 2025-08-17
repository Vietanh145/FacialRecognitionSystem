from facenet_pytorch import MTCNN
import torch
import cv2
import numpy as np
from PIL import Image
import os
from datetime import datetime


def load_model():
    mtcnn = MTCNN(keep_all=True, device='cuda' if torch.cuda.is_available() else 'cpu')
    return mtcnn


def draw_face_features(img, landmarks, box):
    # Vẽ bounding box
    cv2.rectangle(img,
                  (int(box[0]), int(box[1])),
                  (int(box[2]), int(box[3])),
                  (0, 255, 0), 2)

    # Vẽ các điểm landmarks
    for point in landmarks:
        x, y = int(point[0]), int(point[1])
        cv2.circle(img, (x, y), 3, (0, 0, 255), -1)


def detect_landmarks_live():
    mtcnn = load_model()
    cap = cv2.VideoCapture(0)

    cv2.namedWindow('Face Landmarks', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Face Landmarks', 1280, 720)

    save_dir = "saved_faces"
    os.makedirs(save_dir, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không thể đọc từ camera.")
            break

        # Chuyển sang PIL để dùng cho MTCNN
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)

        # Phát hiện khuôn mặt và landmarks
        boxes, probs, landmarks = mtcnn.detect(pil_image, landmarks=True)

        if boxes is not None:
            for box, landmark in zip(boxes, landmarks):
                draw_face_features(frame, landmark, box)

        cv2.imshow('Face Landmarks', frame)
        key = cv2.waitKey(1)

        if key & 0xFF == ord('q'):
            break
        elif key & 0xFF == ord('s'):
            # Lưu ảnh lại với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_dir, f"face_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Ảnh đã được lưu: {filename}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_landmarks_live()
