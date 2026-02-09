from fastapi import APIRouter, FastAPI, Depends, UploadFile, File, status, Request
from fastapi.responses import JSONResponse
import os
from app.helpers.config import get_settings, Settings
from app.controllers import DataController, ProcessController, ProjectController
import aiofiles
from app.models.enums import ResponseEnum
import logging
from app.routes.schemas.data import ProcessRequest
from app.models.ProjectModel import ProjectModel


logger = logging.getLogger('uvicorn.error')  #34an ybnlk fel server el mo4kla

DataRouter = APIRouter(
    prefix="/api/v1/data",
    tags=["/api/v1", "data"],
)


@DataRouter.post("/upload/{Project_ID}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):

    project_model = ProjectModel(
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
    project_dir_path = ProjectController().get_project_path(Project_id=Project_id)
    file_path, file_id = data_controller.generate_uniqe_filepath(
        orig_filename=file.filename,
        project_id=Project_id,
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

    return JSONResponse(
           status_code=status.HTTP_201_CREATED,
           content={
                   "signal": ResponseEnum.FILE_UPLOAD_SUCCESS.value,
                   "file_id": file_id,
                    "project_id": str(project._id)
               }
           )


@DataRouter.post("/process/{Project_ID} ")
async def process_endpoint(Project_id: str, ProcessRequest: ProcessRequest):

    file_id = ProcessRequest.file_id
    chunk_size = ProcessRequest.chunk_size
    overlap_size = ProcessRequest.overlap_size

    process_controller = ProcessController(Project_id=Project_id)

    file_content = process_controller.get_file_content(file_id=file_id)

    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseEnum.PROCESSING_FAILED.value
            }
        )

    return file_chunks







