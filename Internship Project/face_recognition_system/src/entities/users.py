from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from .base import Base
import enum

# Enum định nghĩa role
class UserRole(enum.Enum):
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255))
    image_url = Column(String)
    email = Column(String)
    phone_number = Column(String)
    role = Column(Enum(UserRole), nullable=False)
    ip_address = Column(String)

    logs = relationship('Logs', back_populates='user', cascade='all, delete-orphan')
    leave_requests = relationship('LeaveRequest', back_populates='user', cascade='all, delete-orphan')
