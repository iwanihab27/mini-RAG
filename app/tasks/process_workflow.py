from celery.bin.result import result

from app.celery_app import celery_app, get_setup_utilits
from app.helpers.config import get_settings, Settings
from app.controllers import DataController, ProcessController, ProjectController
from app.models.enums import ResponseEnum
from app.models.enums.AssetTypeEnum import AssetTypeEnum
from app.models.ProjectModel import ProjectModel
from app.models.ChunkModel import ChunkModel
from app.models.AssetModel import AssetModel
from app.models.db_schemas.mini_rag.schemes import Project, datachunk, asset, RetrievedDocuments
from app.stores.LLM.Templates.Template_parser import TemplateParser
from app.routes.schemas.data import ProcessRequest
import asyncio
import logging
from app.controllers.NLPController import NLPController
from celery import chain
from app.tasks.file_processing import process_project_files
from app.tasks.data_indexing import index_data_content
import asyncio

logger = logging.getLogger('__name__')

@celery_app.task(bind=True, name="app.tasks.process_work_flow.process_and_push_task",
                 autoretry_for=(Exception,),
                 retry_kwargs={'max_retries': 3, 'countdown': 60})
def push_after_process(self, prev_task_result):

    project_id = prev_task_result.get("project_id")
    do_reset = prev_task_result.get("do_reset")

    task_results = index_data_content.apply_async(
        kwargs={"project_id": project_id, "do_reset": do_reset}
    )

    return {
        "project_id": project_id,
        "do_reset": do_reset,
        "task_results": (task_results.id)
    }

@celery_app.task(bind=True, name="app.tasks.process_work_flow.process_and_push_workflow",
                 autoretry_for=(Exception,),
                 retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_and_push_workflow(self,  project_id: int, file_id: int, chunk_size: int
                                , overlap_size: int, do_reset: int,):

    workflow = chain(
        process_project_files.s(project_id, file_id, chunk_size, overlap_size, do_reset),
        push_after_process.s()
    )

    result = workflow.apply_async()

    return {
        "signal": "WORKFLOW_STARTED",
        "workflow_id": result.id,
        "tasks": ["app.tasks.file_processing.process_project_files",
                  "app.tasks.data_indexing.index_data_content",]
    }