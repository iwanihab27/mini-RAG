from .mini_rag_base import SQLALchemyBase
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy import Index


class CeleryTaskExecution(SQLALchemyBase):

    __tablename__ = "celery_task_execution"

    execution_id = Column(Integer, primary_key=True, autoincrement=True)

    task_name = Column(String(255), nullable=False)
    task_args_hash = Column(String(64), nullable=False) # SHA-265 hash of task args
    celery_task_id = Column(UUID(as_uuid=True), nullable=False)

    status = Column(String(20), nullable=False, default='PENDING')

    task_args = Column(JSONB, nullable=True)
    result = Column(JSONB, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now, nullable=True)

    __table_args__ = (
        Index('ixz_task_name_args_celery_hash', task_name, task_args_hash, celery_task_id, unique=True),
        Index('ixz_task_execution_status', status),
        Index('ixz_task_execution_created_at', created_at),
        Index('ixz_celery_task_id', celery_task_id),
    )
