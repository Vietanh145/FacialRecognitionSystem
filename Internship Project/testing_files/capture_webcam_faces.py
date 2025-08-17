import cv2
import os
from facenet_pytorch import MTCNN
import time

def capture_faces():
    """Capture face images from webcam"""
    # Initialize MTCNN
    mtcnn = MTCNN(
        image_size=160, margin=0, min_face_size=20,
        thresholds=[0.6, 0.7, 0.7], factor=0.709, post_process=True
    )
    
    # Create directories
    os.makedirs('demo_images/raw_faces/person1', exist_ok=True)
    os.makedirs('demo_images/raw_faces/person2', exist_ok=True)
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("Press 'c' to capture a face image")
    print("Press '1' to save as person1")
    print("Press '2' to save as person2")
    print("Press 'q' to quit")
    
    current_person = 'person1'
    image_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert frame to RGB for MTCNN
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        boxes, _ = mtcnn.detect(frame_rgb)
        
        # Draw boxes around faces
        if boxes is not None:
            for box in boxes:
                box = box.astype(int)
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        
        # Show the frame
        cv2.imshow('Face Capture', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('1'):
            current_person = 'person1'
            print("Switched to person1")
        elif key == ord('2'):
            current_person = 'person2'
            print("Switched to person2")
        elif key == ord('c'):
            if boxes is not None and len(boxes) > 0:
                # Save the frame
                filename = f'demo_images/raw_faces/{current_person}/face_{image_count}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Saved face image to {filename}")
                image_count += 1
            else:
                print("No face detected!")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_faces() 