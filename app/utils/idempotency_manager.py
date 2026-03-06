import hashlib
import json
from datetime import datetime, timedelta
from requests import session
from app.models.db_schemas.mini_rag.schemes.celery_task_execution import CeleryTaskExecution
from sqlalchemy import select, delete
from app.celery_app import celery_app

class IdempotencyManager:

    def __init__(self, db_client, db_engine):

        self.db_client = db_client
        self.db_engine = db_engine

    def create_args_hash(self, task_name: str, task_args: dict):

        combined_data = {
            **task_args,
            "task_name": task_name,
        }

        json_string = json.dumps(combined_data, sort_keys=True, default=str)
        return hashlib.sha256(json_string.encode()).hexdigest() # The hash

    async def create_task_record(self, task_name: str, task_args: dict, celery_task_id: str = None) -> CeleryTaskExecution:

        """Create new task execution record"""
        args_hash = self.create_args_hash(task_name, task_args)

        task_record = CeleryTaskExecution(
            task_name=task_name,
            task_args_hash=args_hash,
            task_args=task_args,
            celery_task_id=celery_task_id,
            status="PENDING",
            started_at=datetime.utcnow(),
        )

        session = self.db_client()
        try:
            session.add(task_record)
            await session.commit()
            await session.refresh(task_record)
            return task_record
        finally:
            await session.close()

    async def update_task_status(self, execution_id: int, status: str, result: dict):

        """update task status and result"""
        session = self.db_client()
        try:
            task_record = await session.get(CeleryTaskExecution, execution_id)
            if task_record:
                task_record.status = status
                if result:
                    task_record.result = result
                if status in ['SUCCESS', 'FAILURE']:
                    task_record.completed_at = datetime.utcnow()
                    await session.commit()
        finally:
            await session.close()

    async def get_existing_task(self, task_name: str, task_args: dict, celery_task_id: str)-> CeleryTaskExecution:

        """check if a task with the same name and args already exists"""
        args_hash = self.create_args_hash(task_name, task_args)

        session = self.db_client()
        try:
            stmt = select(CeleryTaskExecution).where(
                CeleryTaskExecution.celery_task_id == celery_task_id,
                CeleryTaskExecution.task_name == task_name,
                CeleryTaskExecution.task_args_hash == args_hash,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            await session.close()

    async def should_execute_task(self, task_name: str, task_args: dict,
                                        celery_task_id: str,
                                        task_time_limit: int = 600,) -> tuple[bool, CeleryTaskExecution]:

        """
        check if task should be executed or return existing results
        returns (should_execute, existing_task_or_none)
        """
        existing_task = self.get_existing_task(task_name, task_args)

        if not existing_task:
            return True, None

        # do not execute if the task is already completed
        if existing_task.status == "SUCCESS":
            return False, existing_task

        # do not execute if the task is pending or running
        if existing_task.status in ['PENDING', 'STARTED', 'RETRY']:
            if existing_task.started_at:
                time_elapsed = (datetime.utcnow() - existing_task.started_at).total_seconds()
                time_gap = 60
                if time_elapsed > (task_time_limit + time_gap):
                    return True, existing_task
            return False, existing_task

        #RE-execute if previous task is failed
        return True, existing_task

    async def cleanup_old_tasks(self, time_retention: int = 86400) -> int:
        """
        delete old tasks older than time_retention
        args:
             time_retention in seconds 86400 = 24 hours
        Returns:
            num of deleted records
        """
        cutoff = datetime.utcnow() - timedelta(hours=time_retention)

        session = self.db_client()
        try:
            stmt = delete(CeleryTaskExecution).where(
                CeleryTaskExecution.created_at < cutoff,
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount
        finally:
            session.close()


