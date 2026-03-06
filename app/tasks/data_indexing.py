from celery import states
from app.celery_app import celery_app, get_setup_utilits
from app.helpers.config import get_settings, Settings
import asyncio
import logging
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from app.models.ProjectModel import ProjectModel
from app.models.ChunkModel import ChunkModel
from app.controllers.NLPController import NLPController
from app.models.enums import ResponseEnum
from tqdm import tqdm

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.data_indexing.index_data_content",
                 autoretry_for=(Exception,),
                 retry_kwargs={'max_retries': 3, 'countdown': 60})
def index_data_content(self, project_id: int, do_reset: int):

    return asyncio.run(
        _index_data_content(self, project_id, do_reset)
    )

async def _index_data_content(task_instance, project_id: int, do_reset: int):

    db_engine, vectordb_client = None, None

    try:

        (db_engine, db_client, llm_provider_factory, vectordb_provider_factory,
        generation_client, embedding_client, vectordb_client, template_parser) = await get_setup_utilits() # from the startup
                                                                                                           #  of the celery

        logger.warning("setup utils were loaded")

        project_model = await ProjectModel.create_instance(
            db_client=db_client,
        )

        chunkmodel = await ChunkModel.create_instance(
            db_client=db_client,
        )

        project = await project_model.get_project_or_create_one(
            project_id=project_id
        )

        if not project:

            task_instance.update_state(
                state="FAILURE",
                meta={
                "signal": ResponseEnum.PROJECT_NOT_FOUND.value
            }
            )

            raise Exception(f"Project not found for project_id: {project_id}")


        nlp_controller = NLPController(
            vectordb_client=vectordb_client,
            generation_client=generation_client,
            embedding_client=embedding_client,
            TemplateParser=template_parser,
        )

        has_records = True
        page_no = 1
        inserted_items_count = 0
        idx = 0

        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)

        _ = await vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=embedding_client.embedding_size,
            do_reset=do_reset,
        )

        total_chunks_count = await chunkmodel.get_total_chunks_count(project_id=project.project_id)
        pbar = tqdm(total=total_chunks_count, desc="Vector Indexing", position=0)  # progress bar

        while has_records:
            page_chunks = await chunkmodel.get_project_chunks(project_id=project.project_id, page_no=page_no)
            if len(page_chunks):
                page_no += 1
            if not page_chunks or len(page_chunks) == 0:
                has_records = False
                break

            chunk_ids = [c.chunk_id for c in page_chunks]
            idx += len(page_chunks)

            is_inserted = await nlp_controller.index_vector_db(
                project=project,
                chunks=page_chunks,
                chunks_ids=chunk_ids,
            )

            if not is_inserted:

                task_instance.update_state(
                    state="FAILURE",
                    meta={
                        "signal": ResponseEnum.INSERT_INTO_VECTOR_DB_ERROR.value
                    }
                )

                raise Exception(f"can not insert into vectorDB | project_id: {project_id}")

            pbar.update(len(page_chunks))
            inserted_items_count += len(page_chunks)

        task_instance.update_state(
            state="SUCCESS",
            meta={
                "signal": ResponseEnum.INSERT_INTO_VECTOR_DB_SUCCESS.value
            }
        )

        return {
                "signal": ResponseEnum.INSERT_INTO_VECTOR_DB_SUCCESS.value,
                "inserted_items_count": inserted_items_count
            }

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise
    finally:
        try:
            if db_engine:
                await db_engine.dispose()

            if vectordb_client:
                await vectordb_client.disconnect()

        except Exception as e:
            logger.error(f"Task failed while cleaning: {str(e)}")
