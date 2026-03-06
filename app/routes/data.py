from fastapi import APIRouter, FastAPI, Depends, UploadFile, File, status, Request
from fastapi.responses import JSONResponse
import os
from app.helpers.config import get_settings, Settings
from app.controllers import DataController, ProcessController, ProjectController, NLPController
import aiofiles
from app.models.enums import ResponseEnum
import logging
from app.routes.schemas.data import ProcessRequest
from app.models.ProjectModel import ProjectModel
from app.models.db_schemas.mini_rag.schemes import Project, datachunk, asset, RetrievedDocuments
from app.models.ChunkModel import ChunkModel
from app.models.AssetModel import AssetModel
from app.models.enums.AssetTypeEnum import AssetTypeEnum
from app.controllers.NLPController import NLPController
from app.tasks.file_processing import process_project_files
from app.tasks.process_workflow import process_and_push_workflow


logger = logging.getLogger('uvicorn.error')  #34an ybnlk fel server el mo4kla


DataRouter = APIRouter(
    prefix="/api/v1/data",
    tags=["/api/v1", "data"],
)


@DataRouter.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: int, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    data_controller = DataController()
    IsValid, result_signal = data_controller.ValidateUploadedFile(file=file)

    if not IsValid:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
                "signal": result_signal
            }
        )
    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_uniqe_filepath(
        orig_filename=file.filename,
        project_id=project_id,
    )

    try:
        async with aiofiles.open(file_path, mode="wb") as f:
            while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
                await f.write(chunk)  # yfdl ylf w yktb

    except Exception as e:

        logger.error(f"ERROR WHILE UPLOADING FILE: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseEnum.FILE_UPLOAD_FAILED.value
            }
        )

    #store the assets into the DB
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )

    asset_rescource = asset(
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.File.value,
        asset_name=file_id,
        asset_size= os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_rescource)

    return JSONResponse(
           status_code=status.HTTP_201_CREATED,
           content={
                   "signal": ResponseEnum.FILE_UPLOAD_SUCCESS.value,
                   "file_id": str(asset_record.asset_name),
           }
           )


@DataRouter.post("/process/{project_id}")
async def process_endpoint(project_id: int, processRequest: ProcessRequest, request: Request):

    chunk_size = processRequest.chunk_size
    overlap_size = processRequest.overlap_size
    do_reset = processRequest.do_reset

    task = process_project_files.delay(
        project_id=project_id,
        file_id=processRequest.file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        do_reset=do_reset,
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "signal": ResponseEnum.PROCESSING_SUCCESS.value,
            "task_id": task.id,
        }
    )

@DataRouter.post("/process-and-push/{project_id}")
async def process_and_push_endpoint(project_id: int, processRequest: ProcessRequest, request: Request):

    chunk_size = processRequest.chunk_size
    overlap_size = processRequest.overlap_size
    do_reset = processRequest.do_reset

    wokflow_task = process_and_push_workflow.delay(
            project_id=project_id,
            file_id=processRequest.file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            do_reset=do_reset,
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "signal": ResponseEnum.PROCESS_AND_PUSH_WORKFLOW_READY.value,
            "wokflow_task_id": wokflow_task.id,
        }
    )

