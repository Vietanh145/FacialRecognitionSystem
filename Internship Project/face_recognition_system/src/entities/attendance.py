from pydantic import BaseModel
from datetime import datetime

class AttendanceCreate(BaseModel):
    timein: datetime
    timeout: datetime
    status: str
    ip_address: str

class AttendanceResponse(BaseModel):
    id: int
    timein: datetime
    timeout: datetime
    status: str
    ip_address: str

    class Config:
        orm_mode = True