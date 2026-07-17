from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.core.database import Base


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    media_type = Column(String, nullable=False)   # IMAGE / VIDEO / AUDIO
    timestamp = Column(DateTime, default=datetime.utcnow)
    ai_score = Column(String, nullable=False)      # e.g. "87%"
    verdict = Column(String, nullable=False)
    full_result_json = Column(Text, nullable=True)  # complete scan result, for audit/report