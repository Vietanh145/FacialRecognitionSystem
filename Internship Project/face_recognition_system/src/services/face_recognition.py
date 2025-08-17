from typing import Optional
import cv2
import numpy as np
from src.database.models import Attendance
from src.utils.ip_utils import get_client_ip
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.config import DATABASE_URL
from src.entities.account import Account
from src.entities.log import Log
from src.entities.image import Image

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class FaceRecognitionService:
    def __init__(self):
        self.known_faces = []
        self.known_names = []
        self.load_known_faces()

    def load_known_faces(self):
        session = SessionLocal()
        try:
            images = session.query(Image, Account).join(Account, Image.accountid == Account.accountid).all()
            for img, acc in images:
                # Load face embedding from image_url (implement as needed)
                # For demo, just use imagecontext as name
                self.known_names.append(img.imagecontext)
                # self.known_faces.append(face_embedding)
        finally:
            session.close()

    def recognize_face(self, image: np.ndarray) -> dict:
        # Convert the image to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Logic to recognize faces in the image
        # This is a placeholder for actual face recognition logic
        face_locations = []  # Placeholder for detected face locations
        face_encodings = []  # Placeholder for face encodings

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_faces, face_encoding)
            name = "Unknown"

            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_faces, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_names[best_match_index]

        session = SessionLocal()
        try:
            account = session.query(Account).filter_by(accountname=name).first()
            if not account:
                return {"status": "Unknown"}
            # Check if user has checked in today
            today = datetime.now().date()
            log = session.query(Log).filter(Log.accountid==account.accountid, Log.timein>=datetime(today.year, today.month, today.day)).order_by(Log.timein.desc()).first()
            now = datetime.now()
            ip = "127.0.0.1"  # Replace with actual IP if needed
            if not log or log.timeout is not None:
                # Check-in
                new_log = Log(accountid=account.accountid, timein=now, timeout=None, ipaddress=ip, status="Present")
                session.add(new_log)
                session.commit()
                return {"accountid": account.accountid, "name": account.accountname, "role": account.role, "status": "Present", "timein": now, "timeout": None}
            else:
                # Check-out
                log.timeout = now
                log.status = "Absent"
                session.commit()
                return {"accountid": account.accountid, "name": account.accountname, "role": account.role, "status": "Absent", "timein": log.timein, "timeout": now}
        finally:
            session.close()

    def check_in(self, user_name: str, ip_address: str):
        # Logic to handle check-in
        attendance_record = Attendance(timein=datetime.now(), status='Present', ip_address=ip_address)
        # Save attendance_record to the database

    def check_out(self, user_name: str):
        # Logic to handle check-out
        # Update the attendance record for the user
        pass