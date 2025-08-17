from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
import cv2


def load_model():
    mtcnn = MTCNN(image_size=160, margin=20, min_face_size=20,
                  thresholds=[0.6, 0.7, 0.7], factor=0.709, post_process=True, keep_all=False, device='cuda' if torch.cuda.is_available() else 'cpu')
    resnet = InceptionResnetV1(pretrained='vggface2').eval()
    return mtcnn, resnet

def draw_face_features(img, landmarks, box):
    cv2.rectangle(img,
                  (int(box[0]), int(box[1])),
                  (int(box[2]), int(box[3])),
                  (0, 255, 0), 2)

    for point in landmarks:
        cv2.circle(img, (int(point[0]), int(point[1])), 3, (0, 0, 255), -1)
        cv2.circle(img, (int(point[0]), int(point[1])), 4, (255, 255, 255), 1)

    for i in range(len(landmarks) - 1):
        start_point = (int(landmarks[i][0]), int(landmarks[i][1]))
        end_point = (int(landmarks[i + 1][0]), int(landmarks[i + 1][1]))
        cv2.line(img, start_point, end_point, (255, 255, 0), 1)

    if len(landmarks) > 2:
        start_point = (int(landmarks[-1][0]), int(landmarks[-1][1]))
        end_point = (int(landmarks[0][0]), int(landmarks[0][1]))
        cv2.line(img, start_point, end_point, (255, 255, 0), 1)

    if len(landmarks) >= 5:
        left_eye_center = np.mean(landmarks[0:1], axis=0)
        right_eye_center = np.mean(landmarks[1:2], axis=0)
        nose_center = landmarks[2]

        cv2.circle(img, (int(left_eye_center[0]), int(left_eye_center[1])), 5, (0, 255, 255), -1)
        cv2.circle(img, (int(right_eye_center[0]), int(right_eye_center[1])), 5, (0, 255, 255), -1)
        cv2.circle(img, (int(nose_center[0]), int(nose_center[1])), 5, (255, 0, 255), -1)

def get_face_landmarks(image_path, mtcnn):
    img = Image.open(image_path).convert('RGB')
    boxes, probs, landmarks = mtcnn.detect(img, landmarks=True)

    if boxes is None or landmarks is None:
        raise Exception("No face found in the image!")

    return img, boxes[0], landmarks[0]

def visualize_face_comparison(face1_path, face2_path, threshold=0.7):
    mtcnn, resnet = load_model()

    try:
        img1, box1, landmarks1 = get_face_landmarks(face1_path, mtcnn)
        img2, box2, landmarks2 = get_face_landmarks(face2_path, mtcnn)

        img1_np = np.array(img1)
        img2_np = np.array(img2)

        img1_draw = img1_np.copy()
        img2_draw = img2_np.copy()

        draw_face_features(img1_draw, landmarks1, box1)
        draw_face_features(img2_draw, landmarks2, box2)

        # Align faces before passing to resnet
        aligned_face1 = mtcnn(img1)
        aligned_face2 = mtcnn(img2)

        if aligned_face1 is None or aligned_face2 is None:
            raise Exception("Unable to extract aligned faces.")

        embedding1 = resnet(aligned_face1.unsqueeze(0)).detach()
        embedding2 = resnet(aligned_face2.unsqueeze(0)).detach()
        distance = torch.dist(embedding1, embedding2).item()

        plt.figure(figsize=(15, 5))

        plt.subplot(131)
        plt.imshow(cv2.cvtColor(img1_draw, cv2.COLOR_BGR2RGB))
        plt.title('Face 1')
        plt.axis('off')

        plt.subplot(132)
        plt.imshow(cv2.cvtColor(img2_draw, cv2.COLOR_BGR2RGB))
        plt.title('Face 2')
        plt.axis('off')

        plt.subplot(133)
        plt.text(0.1, 0.7, f'Distance: {distance:.4f}', fontsize=12)
        plt.text(0.1, 0.6, f'Threshold: {threshold}', fontsize=12)
        plt.text(0.1, 0.5, f'Result: {"Same person" if distance < threshold else "Different persons"}',
                 fontsize=12, color='green' if distance < threshold else 'red')

        plt.text(0.1, 0.4, 'Legend:', fontsize=12)
        plt.text(0.1, 0.35, '• Green box: Face region', fontsize=10)
        plt.text(0.1, 0.3, '• Red dot: Landmark point', fontsize=10)
        plt.text(0.1, 0.25, '• Yellow line: Connects points', fontsize=10)
        plt.text(0.1, 0.2, '• Yellow dot: Eye center', fontsize=10)
        plt.text(0.1, 0.15, '• Pink dot: Nose center', fontsize=10)

        plt.axis('off')
        plt.suptitle('Detailed Face Comparison', fontsize=16)
        plt.tight_layout()
        plt.show()

        return {
            'distance': distance,
            'is_same_person': distance < threshold,
            'threshold': threshold
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'error': str(e)}


if __name__ == "__main__":
    face1_path = "demo_images/vietanh.JPG"
    face2_path = "demo_images/vietanh2.jpg"

    result = visualize_face_comparison(face1_path, face2_path)
