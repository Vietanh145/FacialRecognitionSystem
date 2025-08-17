import os
import cv2
import torch
import numpy as np
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
from torchvision import datasets
from torch.utils.data import DataLoader

def setup_models():
    """Initialize the face detection and recognition models"""
    # Initialize MTCNN for face detection
    mtcnn = MTCNN(
        image_size=160, margin=0, min_face_size=20,
        thresholds=[0.6, 0.7, 0.7], factor=0.709, post_process=True,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    # Initialize Inception Resnet for face recognition
    resnet = InceptionResnetV1(pretrained='vggface2').eval()
    if torch.cuda.is_available():
        resnet = resnet.cuda()
    
    return mtcnn, resnet

def process_single_image(image_path, mtcnn, resnet):
    """Process a single image for face detection and recognition"""
    # Load image
    img = Image.open(image_path)
    
    # Detect face
    face = mtcnn(img)
    if face is None:
        print(f"No face detected in {image_path}")
        return None
    
    # Get embedding
    face = face.unsqueeze(0)  # Add batch dimension
    if torch.cuda.is_available():
        face = face.cuda()
    
    embedding = resnet(face)
    return embedding

def process_video(video_path, mtcnn, resnet):
    """Process a video file for face tracking"""
    cap = cv2.VideoCapture(video_path)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert frame to PIL Image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        
        # Detect faces
        boxes, _ = mtcnn.detect(pil_img)
        
        if boxes is not None:
            for box in boxes:
                box = box.astype(int)
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow('Face Tracking', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def create_face_dataset(input_dir, output_dir, mtcnn):
    """Create a dataset of aligned face images"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for person_dir in os.listdir(input_dir):
        person_path = os.path.join(input_dir, person_dir)
        if not os.path.isdir(person_path):
            continue
            
        output_person_dir = os.path.join(output_dir, person_dir)
        if not os.path.exists(output_person_dir):
            os.makedirs(output_person_dir)
        
        for img_name in os.listdir(person_path):
            img_path = os.path.join(person_path, img_name)
            try:
                img = Image.open(img_path)
                face = mtcnn(img, save_path=os.path.join(output_person_dir, img_name))
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

def main():
    # Setup models
    print("Initializing models...")
    mtcnn, resnet = setup_models()
    
    # Create directories for demo
    os.makedirs('demo_images', exist_ok=True)
    os.makedirs('demo_videos', exist_ok=True)
    
    # 1. Single Image Processing
    print("\n1. Processing single image...")
    # You'll need to add your own image here
    image_path = 'demo_images/test.jpg'
    if os.path.exists(image_path):
        embedding = process_single_image(image_path, mtcnn, resnet)
        if embedding is not None:
            print("Face embedding shape:", embedding.shape)
    
    # 2. Video Processing
    print("\n2. Processing video...")
    # You'll need to add your own video here
    video_path = 'demo_videos/test.mp4'
    if os.path.exists(video_path):
        process_video(video_path, mtcnn, resnet)
    
    # 3. Create Face Dataset
    print("\n3. Creating face dataset...")
    input_dir = 'demo_images/raw_faces'
    output_dir = 'demo_images/aligned_faces'
    if os.path.exists(input_dir):
        create_face_dataset(input_dir, output_dir, mtcnn)

if __name__ == "__main__":
    main() 