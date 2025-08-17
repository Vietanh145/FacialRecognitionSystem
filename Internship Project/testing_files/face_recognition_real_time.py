import asyncio
import platform
import os
import time
import logging
import numpy as np
import cv2
from PIL import Image
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='face_recognition_combined.log',
    filemode='a'
)


def check_image_quality(image_path):
    """Check image quality before processing"""
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
    """Load MTCNN and InceptionResnetV1 models"""
    mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20,
                  thresholds=[0.7, 0.8, 0.8], factor=0.709, post_process=True)
    resnet = InceptionResnetV1(pretrained='vggface2').eval()
    return mtcnn, resnet

#Extract face vector from an image
def get_face_vector(image, mtcnn, resnet, is_pil=False):
    try:
        if is_pil:
            img = image
        else:
            img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        face, prob = mtcnn(img, return_prob=True)
        if face is None or prob < 0.95:
            return None, None, prob

        logging.info(f"Face detection confidence: {prob:.2f}")

        embedding = resnet(face.unsqueeze(0)).detach()
        embedding = embedding / torch.norm(embedding, p=2, dim=1, keepdim=True)
        return embedding.numpy().flatten(), face, prob
    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        return None, None, None


def load_face_database(database_path, mtcnn, resnet):
    """Load face vectors from database folder, returning individual and averaged vectors"""
    database = {}
    image_vectors = {}
    image_paths = []
    image_names = []
    for person_folder in os.listdir(database_path):
        person_path = os.path.join(database_path, person_folder)
        if not os.path.isdir(person_path):
            continue
        embeddings = []
        for img_file in os.listdir(person_path):
            img_path = os.path.join(person_path, img_file)
            try:
                if check_image_quality(img_path):
                    img = Image.open(img_path).convert('RGB')
                    vector, _, prob = get_face_vector(img, mtcnn, resnet, is_pil=True)
                    if vector is not None:
                        embeddings.append(vector)
                        image_paths.append(img_path)
                        image_vectors[img_path] = vector
                        image_names.append(f"{person_folder}/{img_file}")
                        logging.info(f"Loaded embedding for {img_path}: {vector[:10]}...")
                    else:
                        logging.warning(f"No face detected or low confidence in {img_path}")
            except Exception as e:
                logging.error(f"Error loading image {img_path}: {str(e)}")
        if embeddings:
            database[person_folder] = np.mean(embeddings, axis=0)
    logging.info(f"Loaded {len(image_vectors)} images and {len(database)} persons")
    return database, image_paths, image_vectors, image_names


def save_captured_data(frame, vector, save_dir="captured_data"):
    """Save captured frame and vector"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    image_path = os.path.join(save_dir, f"captured_{timestamp}.jpg")
    cv2.imwrite(image_path, frame)
    logging.info(f"Saved captured image to {image_path}")

    vector_path = os.path.join(save_dir, f"vector_{timestamp}.log")
    vector_str = ",".join(map(str, vector))
    with open(vector_path, 'w') as f:
        f.write(vector_str)
    logging.info(f"Saved vector to {vector_path}")
    return image_path


def compare_vectors(database, database_paths, image_vectors, image_names, captured_vector, captured_image_path,
                    threshold=0.35):
    """Compare captured vector with database vectors"""
    valid_vectors = [image_vectors[path] for path in database_paths if path in image_vectors]
    valid_paths = [path for path in database_paths if path in image_vectors]
    valid_names = image_names
    valid_vectors.append(captured_vector)
    valid_paths.append(captured_image_path)
    valid_names.append('Captured')

    # Debugging: Log lengths to diagnose mismatches
    logging.info(f"compare_vectors: {len(valid_vectors)} vectors, {len(valid_paths)} paths, {len(valid_names)} names")

    if not (len(valid_vectors) == len(valid_paths) == len(valid_names)):
        logging.error("Mismatch in lengths: vectors=%d, paths=%d, names=%d",
                      len(valid_vectors), len(valid_paths), len(valid_names))
        raise ValueError("Mismatch in number of vectors, paths, and names")

    # Determine matches
    is_same_person = []
    for name in database.keys():
        dist = cosine(database[name], captured_vector)
        same = dist < threshold
        confidence = 1 - dist
        logging.info(f"Comparing {name} with Captured: "
                     f"Cosine Distance = {dist:.4f}, "
                     f"Confidence = {confidence:.4f}, "
                     f"Result = {'Same person' if same else 'Different person'}")
        is_same_person.append((name, dist, confidence, same))

    return is_same_person, valid_vectors, image_vectors


async def main(database_path="demo_images", threshold=0.35, save_dir="captured_data"):
    """Main function for real-time face recognition and comparison"""
    mtcnn, resnet = load_model()

    # Load face database
    logging.info("Loading face database...")
    database, database_paths, image_vectors, image_names = load_face_database(database_path, mtcnn, resnet)
    if not database:
        logging.error("No faces loaded into the database.")
        return

    # Print vectors for each image in the database
    print("\nDatabase Image Vectors:")
    for img_path, vector in image_vectors.items():
        print(f"Vector for {img_path}: {vector[:10]}... (length: {len(vector)})")

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Could not open webcam.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logging.error("Failed to capture frame from webcam.")
                break

            # Detect faces in the frame
            try:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                boxes, probs = mtcnn.detect(img)
            except Exception as e:
                logging.error(f"Error detecting faces in frame: {str(e)}")
                continue

            if boxes is not None:
                for box, prob in zip(boxes, probs):
                    if prob < 0.95:
                        continue
                    x1, y1, x2, y2 = map(int, box)

                    # Extract embedding for the detected face
                    vector, _, _ = get_face_vector(frame[y1:y2, x1:x2], mtcnn, resnet)
                    if vector is None:
                        continue

                    # Compare with database
                    min_dist = float('inf')
                    identity = "Unknown"
                    for name, db_vector in database.items():
                        dist = cosine(vector, db_vector)
                        if dist < min_dist and dist < threshold:
                            min_dist = dist
                            identity = name

                    # Draw bounding box and label
                    color = (0, 255, 0) if identity != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{identity}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                    # Save and compare on 's' key
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('s'):
                        captured_image_path = save_captured_data(frame, vector, save_dir)
                        print(f"\nCaptured Vector: {vector[:10]}... (length: {len(vector)})")
                        try:
                            results, vectors, image_vectors = compare_vectors(
                                database, database_paths, image_vectors, image_names, vector, captured_image_path,
                                threshold)
                            print("\nComparison results:")
                            for name, dist, conf, same in results:
                                print(f"Captured vs {name}:")
                                print(f"  Cosine Distance: {dist:.4f}")
                                print(f"  Confidence: {conf:.4f}")
                                print(f"  Result: {'Same person' if same else 'Different person'}\n")
                        except ValueError as e:
                            logging.error(f"Error in compare_vectors: {str(e)}")

            # Display the frame
            cv2.imshow('Face Recognition', frame)

            # Quit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            await asyncio.sleep(1.0 / 30)  # Control frame rate (30 FPS)

    finally:
        cap.release()
        cv2.destroyAllWindows()


if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())