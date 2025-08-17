import os
import cv2
import shutil
import requests
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
from datetime import datetime
import threading
import time

import torch
from torchvision import transforms
from facenet_pytorch import MTCNN, InceptionResnetV1

from sklearn.metrics.pairwise import cosine_similarity

import psycopg2
from psycopg2 import Error
from db_config import DB_CONFIG

def load_known_faces():
    image_folder = "known_faces"
    os.makedirs(image_folder, exist_ok=True)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    mtcnn = MTCNN(image_size=160, margin=20, min_face_size=20, thresholds=[0.7, 0.8, 0.8], device=device)
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

    known_face_embeddings = []
    known_face_names = []

    transform = transforms.Compose([
        transforms.Resize((160, 160)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_name, image_url 
            FROM users
        """)
        rows = cursor.fetchall()

        for name, image_url in rows:
            local_path = os.path.join(image_folder, f"{name}_{os.path.basename(image_url)}")
            try:
                if image_url and image_url.startswith(('http://', 'https://')):
                    resp = requests.get(image_url, stream=True, timeout=10)
                    if resp.status_code == 200:
                        with open(local_path, 'wb') as f:
                            resp.raw.decode_content = True
                            shutil.copyfileobj(resp.raw, f)
                    else:
                        continue
                else:
                    if image_url and os.path.exists(image_url):
                        shutil.copy(image_url, local_path)
                    else:
                        continue

                img = Image.open(local_path).convert('RGB')
                boxes, _ = mtcnn.detect(img)

                if boxes is not None:
                    box = boxes[0]
                    face = img.crop((
                        max(0, int(box[0])),
                        max(0, int(box[1])),
                        min(img.width, int(box[2])),
                        min(img.height, int(box[3]))
                    ))
                    face_processed = transform(face)
                    emb = resnet(face_processed.unsqueeze(0).to(device))
                    emb = torch.nn.functional.normalize(emb, p=2, dim=1)
                    known_face_embeddings.append(emb[0].detach().cpu())
                    known_face_names.append(name)

            except Exception:
                continue

        return known_face_embeddings, known_face_names

    except (Exception, Error) as e:
        print(f"DB load error: {str(e)}")
        return [], []
    finally:
        if conn:
            cursor.close()
            conn.close()

class FaceRecognitionSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("FACE RECOGNITION SYSTEM")
        self.root.geometry("1400x800")
        self.db_config = DB_CONFIG

        self.init_database()
        self.main = ttk.Frame(self.root)
        self.main.pack(fill='both', expand=True, padx=10, pady=5)

        self.setup_camera_frame()
        self.setup_info_frame()

        self.cap = None
        self.is_camera_running = False
        self.processing_face = False

        self.known_face_encodings, self.known_face_names = load_known_faces()

        self.device = None
        self.mtcnn = None
        self.resnet = None
        self.recognized_box_info = []

        self.start_time = None
        self.duration_updating = False

    def setup_camera_frame(self):
        frm = ttk.LabelFrame(self.main, text="Camera Feed")
        frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.camera_label = ttk.Label(frm)
        self.camera_label.pack(pady=10)
        ctr = ttk.Frame(frm)
        ctr.pack(fill=tk.X, pady=5)
        ttk.Button(ctr, text="Start Camera", command=self.start_camera).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctr, text="Stop Camera", command=self.stop_camera).pack(side=tk.LEFT, padx=5)

    def setup_info_frame(self):
        frm = ttk.LabelFrame(self.main, text="PERSONAL INFORMATION", style='Info.TLabelframe')
        frm.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        style = ttk.Style()
        style.configure('Info.TLabelframe.Label', font=('Arial', 14, 'bold'))

        self.info_labels = {}
        fields = ['ID', 'Name', 'Role', 'Status']
        for f in fields:
            sub = ttk.Frame(frm)
            sub.pack(fill=tk.X, pady=5, padx=10)
            ttk.Label(sub, text=f"{f}:", font=('Arial', 12, 'bold'), width=15).pack(side=tk.LEFT)
            lbl = ttk.Label(sub, text='No Data', font=('Arial', 11))
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.info_labels[f] = lbl
        ttk.Separator(frm).pack(fill=tk.X, pady=10, padx=5)
        self.status_lbl = ttk.Label(frm, text="Recognition Status: Waiting...", font=('Arial', 12, 'bold'))
        self.status_lbl.pack(pady=5, padx=10)

        self.duration_label = ttk.Label(frm, text="Duration: 0.0s", font=('Arial', 11, 'italic'))
        self.duration_label.pack(pady=5, padx=10)

    def update_duration(self):
        if self.duration_updating and self.start_time:
            elapsed = time.time() - self.start_time
            self.duration_label.configure(text=f"Duration: {elapsed:.1f}s")
            self.root.after(100, self.update_duration)

    def update_info_display(self, data):
        try:
            if data and isinstance(data, dict):
                value_map = {
                    'ID': data.get('ID', 'N/A'),
                    'Name': data.get('Name', 'N/A'),
                    'Role': data.get('Role', 'N/A'),
                    'Status': data.get('Status', 'N/A')
                }

                timein = data.get('time_in')
                timeout = data.get('time_out')
                status_text = ""
                late_time = datetime.strptime("08:00:00", "%H:%M:%S").time()

                if timein and not timeout:
                    timein_dt = datetime.fromisoformat(timein)
                    timein_fmt = timein_dt.strftime('%Y-%m-%d %H:%M:%S')
                    if timein_dt.time() > late_time:
                        status_text = f"Late: {timein_fmt}"
                        value_map['Status'] = "Late"
                    else:
                        status_text = f"Check-in: {timein_fmt}"
                        value_map['Status'] = "Check-in"
                elif timein and timeout:
                    timeout_fmt = datetime.fromisoformat(timeout).strftime('%Y-%m-%d %H:%M:%S')
                    status_text = f"Check-out: {timeout_fmt}"
                    value_map['Status'] = "Check-out"
                else:
                    status_text = "Recognition Status: Identified"
                    value_map['Status'] = "Identified"

                for key in self.info_labels:
                    self.info_labels[key].configure(text=value_map[key])

                self.status_lbl.configure(text=status_text, foreground='green')
            else:
                raise ValueError("Empty data")
        except Exception:
            for lbl in self.info_labels.values():
                lbl.configure(text='No Data')
            self.status_lbl.configure(text="Recognition Status: Unknown Face Detected", foreground='red')

    def reset_info_display(self):
        for lbl in self.info_labels.values():
            lbl.configure(text='No Data')
        self.status_lbl.configure(text="Recognition Status: Waiting...", foreground='black')

    def init_database(self):
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_name VARCHAR(255),
                    image_url VARCHAR(255),
                    email VARCHAR(255),
                    phone_number VARCHAR(50),
                    role VARCHAR(100),
                    ip_address VARCHAR(100),
                    status VARCHAR(50)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id),
                    date DATE,
                    time_in TIMESTAMP, 
                    time_out TIMESTAMP,
                    status VARCHAR(50)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id),
                    start_date DATE,
                    end_date DATE,
                    reason TEXT,
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            if conn:
                cur.close()
                conn.close()

    def start_camera(self):
        if self.is_camera_running:
            return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera!")
            return

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.mtcnn = MTCNN(image_size=160, margin=0, keep_all=True, thresholds=[0.6, 0.7, 0.7],
                           factor=0.709, device=self.device)
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)

        self.is_camera_running = True
        self.recognized_box_info.clear()
        self.start_time = time.time()
        self.duration_updating = True
        self.update_duration()
        self.update_camera()

    def stop_camera(self):
        self.is_camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
            cv2.destroyAllWindows()
        self.camera_label.configure(image='')
        self.recognized_box_info.clear()
        self.reset_info_display()
        self.duration_updating = False
        self.start_time = None
        self.duration_label.configure(text="Duration: 0.0s")

    def update_camera(self):
        if not self.is_camera_running or not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if ret:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                boxes, probs = self.mtcnn.detect(pil_img)
                draw = ImageDraw.Draw(pil_img)

                if boxes is not None:
                    new_box_info = []
                    for i, (box, prob) in enumerate(zip(boxes, probs)):
                        if prob > 0.90:
                            box = [int(b) for b in box]
                            name, score = "Detecting", 0.0
                            if i < len(self.recognized_box_info):
                                name, score = self.recognized_box_info[i][1], self.recognized_box_info[i][2]
                            else:
                                # Khởi động lại thời gian khi phát hiện khuôn mặt mới
                                self.start_time = time.time()
                                self.duration_updating = True
                                self.update_duration()  # Gọi lại để bắt đầu đếm thời gian

                            new_box_info.append((box, name, score))

                            if not self.processing_face and name == "Detecting":
                                self.processing_face = True
                                threading.Thread(target=self.process_face, args=(pil_img.copy(), box, i)).start()

                    self.recognized_box_info = new_box_info

                    for box, name, score in self.recognized_box_info:
                        color = 'red' if name == "Unknown" else 'cyan'
                        label = f"{name}" if name in ["Unknown", "Detecting"] else f"{name} ({score:.2f})"
                        draw.rectangle(box, outline=color, width=3)
                        draw.text((box[0], box[1] - 10), label, fill=color)
                else:
                    # Reset thời gian và thông tin khi không còn khuôn mặt
                    self.recognized_box_info.clear()
                    self.reset_info_display()
                    self.start_time = None
                    self.duration_updating = False
                    self.duration_label.configure(text="Duration: 0.0s")

                imgtk = ImageTk.PhotoImage(pil_img)
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)
            except Exception as ex:
                print(f"Error in camera loop: {ex}")
                self.update_info_display(None)

        self.root.after(10, self.update_camera)

    def process_face(self, pil_img, box, box_index):
        start_time = time.time()
        try:
            face = pil_img.crop((int(box[0]), int(box[1]), int(box[2]), int(box[3])))
            transform = transforms.Compose([
                transforms.Resize((160, 160)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
            ])
            face_tensor = transform(face).unsqueeze(0).to(self.device)
            with torch.no_grad():
                emb = self.resnet(face_tensor)
                emb = torch.nn.functional.normalize(emb, p=2, dim=1).cpu().numpy()

            known_emb = [e.cpu().numpy() for e in self.known_face_encodings]
            if known_emb:
                sims = cosine_similarity(emb, known_emb)[0]
                idx = int(np.argmax(sims))
                score = sims[idx]
                if score > 0.7:
                    name = self.known_face_names[idx]
                    conn = psycopg2.connect(**self.db_config)
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM users WHERE user_name = %s", (name,))
                    row = cur.fetchone()
                    cur.close()
                    conn.close()
                    if row:
                        user_id = row[0]
                        resp = requests.post('http://localhost:8000/attendance/checkin',
                                             json={"user_id": user_id})
                        if resp.status_code == 200:
                            data = resp.json()
                            self.root.after(0, self.update_info_display, {
                                'ID': data.get('user_id', ''),
                                'Name': data.get('user_name', name),
                                'Role': data.get('role', ''),
                                'Status': data.get('status', ''),
                                'time_in': data.get('time_in', ''),
                                'time_out': data.get('time_out', ''),
                                'score': f"{score:.2f}"
                            })
                            self.duration_updating = False  # Dừng thời gian sau khi hiển thị thông tin
                            self.root.after(0, self.set_recognized_info, (box, name, score, box_index))
                            return

            if time.time() - start_time > 2:
                self.root.after(0, self.update_info_display, None)
                self.root.after(0, self.set_recognized_info, (box, "Unknown", 0.0, box_index))
                return
            if not known_emb:
                self.root.after(0, self.update_info_display, None)
                self.root.after(0, self.set_recognized_info, (box, "Unknown", 0.0, box_index))
        except Exception as e:
            print("Face process error:", e)
            self.root.after(0, self.update_info_display, None)
            self.root.after(0, self.set_recognized_info, (box, "Unknown", 0.0, box_index))
        finally:
            self.processing_face = False

    def set_recognized_info(self, box_info):
        box, name, score, index = box_info
        if index < len(self.recognized_box_info):
            self.recognized_box_info[index] = (box, name, score)

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionSystem(root)
    root.mainloop()