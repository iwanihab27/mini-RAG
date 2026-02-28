from .mini_rag_base import SQLALchemyBase
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from pydantic import BaseModel


class datachunk(SQLALchemyBase):

    __tablename__ = "chunk"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    chunk_text = Column(String, nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)
    chunk_order = Column(Integer, nullable=False)

    chunk_project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    chunk_asset_id = Column(Integer, ForeignKey('assets.asset_id'), nullable=False)

    create_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    project = relationship("Project", back_populates="chunk")
    asset = relationship("asset", back_populates="chunk")

    __table_args__ = (
        Index('ix_chunk_project_id', chunk_project_id),
        Index('ix_chunk_asset_id', chunk_asset_id),
    )


class RetrievedDocuments(BaseModel):
    text: str
    score: float
