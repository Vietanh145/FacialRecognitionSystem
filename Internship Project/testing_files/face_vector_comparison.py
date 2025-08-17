from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import logging
from scipy.spatial.distance import cosine
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='face_comparison.log',
    filemode='a'
)

def check_image_quality(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise Exception("Could not read image")
        height, width = img.shape[:2]
        if width < 50 or height < 50:
            raise Exception(f"Image too small: {width}x{height}")
        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
        if laplacian_var < 50:
            raise Exception(f"Image too blurry (Laplacian variance: {laplacian_var:.2f})")
        logging.info(f"Image quality check passed for {image_path}: Size={width}x{height}, Blur={laplacian_var:.2f}")
        return True
    except Exception as e:
        logging.error(f"Image quality check failed for {image_path}: {str(e)}")
        return False

def load_model():
    mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20,
                  thresholds=[0.7, 0.8, 0.8], factor=0.709, post_process=True)
    resnet = InceptionResnetV1(pretrained='vggface2').eval()
    return mtcnn, resnet

def get_face_vector(image_path, mtcnn, resnet):
    try:
        if not check_image_quality(image_path):
            logging.warning(f"Proceeding with face detection despite quality check failure for {image_path}")
        img = Image.open(image_path).convert('RGB')
        face, prob = mtcnn(img, return_prob=True)
        if face is None or prob < 0.95:
            raise Exception(f"No face found or low confidence ({prob:.2f}) in image {image_path}")
        logging.info(f"Face detection confidence for {image_path}: {prob:.2f}")
        embedding = resnet(face.unsqueeze(0)).detach()
        embedding = embedding / torch.norm(embedding, p=2, dim=1, keepdim=True)
        return embedding.numpy().flatten()
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {str(e)}")
        raise

def compare_multiple_faces(image_paths, threshold=0.35):
    mtcnn, resnet = load_model()
    vectors = []
    images = []

    for i, path in enumerate(image_paths):
        try:
            vector = get_face_vector(path, mtcnn, resnet)
            vectors.append(vector)
            images.append(Image.open(path))
            logging.info(f"Image {i + 1} vector ({path}): {vector[:10]}...")
        except Exception as e:
            return {'error': f"Error processing image {path}: {str(e)}"}

    n = len(vectors)
    distance_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            distance_matrix[i, j] = cosine(vectors[i], vectors[j])

    # Tính toán khoảng cách và confidence
    is_same_person = []
    result_text = ""
    for i in range(n):
        for j in range(i + 1, n):
            dist = distance_matrix[i, j]
            confidence = 1 - dist
            same = dist < threshold
            result_text = f"Cosine Distance: {dist:.4f}\nConfidence: {confidence:.4f}\nResult: {'Same person' if same else 'Different person'}"
            logging.info(f"Comparing Image {i + 1} and Image {j + 1}: Cosine Distance = {dist:.4f}, Confidence = {confidence:.4f}, Result = {'Same' if same else 'Different'}")
            is_same_person.append((i + 1, j + 1, dist, confidence, same))

    # Hiển thị ảnh + bounding box + chỉ số trực tiếp
    plt.figure(figsize=(15, 8))
    for i, img in enumerate(images):
        plt.subplot(1, n, i + 1)
        plt.imshow(img)
        plt.title(f'Image {i + 1}')
        plt.axis('off')
        boxes, _ = mtcnn.detect(img)
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = box
                width, height = x2 - x1, y2 - y1
                rect = Rectangle((x1, y1), width, height, linewidth=2, edgecolor='red', facecolor='none')
                plt.gca().add_patch(rect)
        if n == 2:
            plt.text(5, 10, result_text, fontsize=10, color='blue', backgroundcolor='white', verticalalignment='top')

    plt.tight_layout()
    plt.show()

    # Heatmap Cosine Distance
    plt.figure(figsize=(6, 5))
    sns.heatmap(distance_matrix, annot=True, fmt='.4f', cmap='Blues',
                xticklabels=[f'Image {i + 1}' for i in range(n)],
                yticklabels=[f'Image {i + 1}' for i in range(n)])
    plt.title(f'Cosine Distance Matrix\nThreshold: {threshold}')
    plt.tight_layout()
    plt.show()

    # Biểu đồ vector khác nhau
    if n == 2:
        diff_vector = np.abs(vectors[0] - vectors[1])
        plt.figure(figsize=(12, 4))
        plt.plot(diff_vector, color='purple', label='|Vector1 - Vector2|')
        plt.title('Absolute Differences Between Two Face Embeddings')
        plt.xlabel('Embedding Dimensions')
        plt.ylabel('Difference')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    return {
        'distance_matrix': distance_matrix,
        'is_same_person': is_same_person,
        'threshold': threshold,
        'vectors': vectors
    }

if __name__ == "__main__":
    image_paths = [
        # "demo_images/Viet_Anh/nguyenvietanh02.jpg",
        "demo_images/Xoai/Hoai_Anh.JPG",
        "demo_images/Viet_Anh/vietanh.JPG",
    ]

    result = compare_multiple_faces(image_paths, threshold=0.35)

    if 'error' not in result:
        print("\nComparison results:")
        for i, j, dist, conf, same in result['is_same_person']:
            print(f"Image {i} vs Image {j}:")
            print(f"  Cosine Distance: {dist:.4f}")
            print(f"  Confidence: {conf:.4f}")
            print(f"  Result: {'Same person' if same else 'Different person'}\n")
    else:
        print(result['error'])
