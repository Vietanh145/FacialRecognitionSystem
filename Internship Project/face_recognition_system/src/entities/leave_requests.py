from sqlalchemy import Column, Integer, ForeignKey, Date, TIMESTAMP, Text, Enum
from sqlalchemy.orm import relationship
from .base import Base
import enum

class LeaveStatus(enum.Enum):
    CHECKIN = "CHECKIN"
    LATE = "LATE"
    CHECKOUT = "CHECKOUT"
    NOTCHECKOUT = "NOTCHECKOUT"

def get_leave_status_message(status: LeaveStatus) -> str:
    if status == LeaveStatus.CHECKIN:
        return "Employee has checked in."
    elif status == LeaveStatus.LATE:
        return "Employee checked in late."
    elif status == LeaveStatus.CHECKOUT:
        return "Employee has checked out."
    elif status == LeaveStatus.NOTCHECKOUT:
        return "Employee has not checked out."
    else:
        return "Unknown status."

class LeaveRequest(Base):
    __tablename__ = 'leave_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    start_date = Column(Date)
    end_date = Column(Date)
    reason = Column(Text)
    status = Column(Enum(LeaveStatus), nullable=False)
    created_at = Column(TIMESTAMP)

    user = relationship('Users', back_populates='leave_requests')
