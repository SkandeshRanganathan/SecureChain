from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hex
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    custody_logs = relationship(
        "CustodyLog",
        back_populates="evidence",
        cascade="all, delete-orphan",
        order_by="CustodyLog.timestamp",
    )


class CustodyLog(Base):
    __tablename__ = "custody_log"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(32), nullable=False)  # e.g., UPLOAD, ACCESS
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    details = Column(Text, nullable=True)

    previous_hash = Column(String(128), nullable=False)
    current_hash = Column(String(128), nullable=False, index=True)

    evidence = relationship("Evidence", back_populates="custody_logs")

