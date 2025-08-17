from sqlalchemy import Column, Integer, String, ForeignKey, Date, TIMESTAMP
from sqlalchemy.orm import relationship
from .base import Base

class Logs(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date)
    time_in = Column(TIMESTAMP)
    time_out = Column(TIMESTAMP)
    status = Column(String)

    user = relationship('Users', back_populates='logs')
