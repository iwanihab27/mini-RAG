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
from app.models.db_schemas import DataChunk, Asset
from app.models.ChunkModel import ChunkModel
from app.models.AssetModel import AssetModel
from app.models.enums.AssetTypeEnum import AssetTypeEnum



logger = logging.getLogger('uvicorn.error')  #34an ybnlk fel server el mo4kla


DataRouter = APIRouter(
    prefix="/api/v1/data",
    tags=["/api/v1", "data"],
)


@DataRouter.post("/upload/Project_ID")
async def upload_data(request: Request, project_id: str, file: UploadFile,
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
    asset_rescource = Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.File.value,
        asset_name=file_id,
        asset_size= os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_rescource)

    return JSONResponse(
           status_code=status.HTTP_201_CREATED,
           content={
                   "signal": ResponseEnum.FILE_UPLOAD_SUCCESS.value,
                   "file_id": str(asset_record.id),
           }
           )


@DataRouter.post("/process/Project_ID ")
async def process_endpoint(Project_ID: str, processRequest: ProcessRequest, request: Request):

    file_id = processRequest.file_id
    chunk_size = processRequest.chunk_size
    overlap_size = processRequest.overlap_size
    do_reset = processRequest.do_reset

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=Project_ID
    )

    process_controller = ProcessController(project_id=Project_ID)

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

    file_chunks_record = [
        DataChunk(
            chunk_text = chunk.page_content,
    chunk_metadata = chunk.metadata,
    chunk_order = i+i,
    chunk_project_id = project.id,
    )

        for i, chunk in enumerate(file_chunks)
    ]

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )

    no_records = await chunk_model.insert_many_chunks(chunks=file_chunks_record)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "signal": ResponseEnum.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records
                 }

        )







