from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    file_path = Column(String, nullable=False)  # local or S3
    storage_type = Column(String, nullable=False)  # 'local' or 's3'
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)
    # chunks = relationship("DocumentChunk", back_populates="document")  # Uncomment when DocumentChunk is defined 