from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON, Text, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    
    doc_id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_task_id = Column(String, nullable=True)
    processing_results = Column(JSON, nullable=True)  # Store processing statistics
    file_size = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)  # Processing time in seconds
    ingest_time = Column(Float, nullable=True)  # LightRAG ingestion time
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
