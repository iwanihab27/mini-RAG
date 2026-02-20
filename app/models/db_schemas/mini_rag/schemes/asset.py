from .mini_rag_base import SQLALchemyBase
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy import Index


class asset(SQLALchemyBase):

    __tablename__ = "assets"

    asset_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    asset_type = Column(String, nullable=False)
    asset_name = Column(String, nullable=False)
    asset_size = Column(Integer, nullable=False)
    asset_config = Column(JSONB, nullable=True)

    asset_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)

    create_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    project = relationship("Project", back_populates="asset")
    chunk = relationship("datachunk", back_populates="asset")

    __table_args__ = (
        Index('ix_asset_project_id', asset_project_id),
        Index('ix_asset_type', asset_type),
    )