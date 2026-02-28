from .mini_rag_base import SQLALchemyBase
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship


class Project(SQLALchemyBase):

    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    create_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    chunk = relationship("datachunk", back_populates="project")
    asset = relationship("asset", back_populates="project")

    

