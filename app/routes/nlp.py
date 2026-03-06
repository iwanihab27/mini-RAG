from fastapi import APIRouter, FastAPI, Depends, UploadFile, File, status, Request
from fastapi.responses import JSONResponse
import logging
from app.routes.schemas.nlp import PushRequest, SearchRequest
from app.models import ProjectModel, ChunkModel
from app.controllers.NLPController import NLPController
from app.models.enums import ResponseEnum
from app.models.ProjectModel import ProjectModel
from app.models.ChunkModel import ChunkModel
import json
from tqdm.auto import tqdm
from app.tasks.data_indexing import index_data_content


logger = logging.getLogger('uvicorn.error')

NLPRouter = APIRouter(
    prefix="/nlp",
    tags=['nlp'],
)


@NLPRouter.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: int, push_request: PushRequest):

    task = index_data_content.delay(
        project_id=project_id,
        do_reset=push_request.do_reset,
    )

    return JSONResponse(
        content={
            "signal": ResponseEnum.DATA_PUSH_TASK_READY.value,
            "task_id": task.id
        }
    )

@NLPRouter.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        TemplateParser=request.app.TemplateParser,
    )

    collection_info = await nlp_controller.get_vector_collection_info(project=project)

    return JSONResponse(
        content={
            "signal": ResponseEnum.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info
        }
    )

@NLPRouter.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: int, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        TemplateParser=request.app.TemplateParser,
    )

    results = await nlp_controller.search_vector_db_collection(
        project=project, text=search_request.text, limit=search_request.limit
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseEnum.VECTORDB_SEARCH_ERROR.value,
            }
        )

    return JSONResponse(
        content={
            "signal": ResponseEnum.VECTORDB_SEARCH_SUCCESS.value,
            "results": [ result.dict() for result in results ]
        }
    )

@NLPRouter.post("/index/answer/{project_id}")
async def answer_index(request: Request, project_id: int, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client,
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        TemplateParser=request.app.TemplateParser,
    )

    answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseEnum.RAG_ANSWER_ERROR.value
            })

    return JSONResponse(
        content={
            "signal": ResponseEnum.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        })





