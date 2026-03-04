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

logger = logging.getLogger('__name__')


@celery_app.task(bind=True, name="app.tasks.file_processing.process_project_files",
                 autoretry_for=(Exception,),
                 retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_project_files(self, project_id: int, file_id: int, chunk_size: int
                                , overlap_size: int, do_reset: int,):

    asyncio.run(
        _process_project_files(self, project_id, file_id, chunk_size,
                                     overlap_size, do_reset)
    )


async def _process_project_files(task_instance, project_id: int,
                                 file_id: int, chunk_size: int
                                , overlap_size: int, do_reset: int,):

    db_engine, vectordb_client = None, None

    try:

        (db_engine, db_client, llm_provider_factory, vectordb_provider_factory,
        generation_client, embedding_client, vectordb_client, template_parser) = await get_setup_utilits() # from the startup
                                                                                                    #  of the celery

        project_model = await ProjectModel.create_instance(
            db_client=db_client
        )

        project = await project_model.get_project_or_create_one(
            project_id=project_id
        )

        nlp_controller = NLPController(
            vectordb_client=vectordb_client,
            generation_client=generation_client,
            embedding_client=embedding_client,
            TemplateParser=template_parser,
        )

        asset_model = await AssetModel.create_instance(
            db_client=db_client
        )

        project_file_ids = {}
        if file_id:
            asset_record = await asset_model.get_asset_record(
                asset_project_id=project.project_id,
                asset_name=file_id
            )

            if asset_record is None:
                task_instance.update_state(
                    state="FAILURE",
                    metadata={
                        "signal": ResponseEnum.FILE_ID_ERROR.value,
                    }
                )

                raise Exception(f"No assets for file:{file_id}")

            project_file_ids = {
                asset_record.asset_id: asset_record.asset_name
            }
        else:

            project_files = await asset_model.get_all_project_assets(
                asset_project_id=project.project_id,
                asset_type=AssetTypeEnum.File.value,
            )

            project_file_ids = {
                record.asset_id: record.asset_name
                for record in project_files
            }

        if len(project_file_ids) == 0:
            task_instance.update_state(
                state="FAILURE",
                metadata={
                    "signal": ResponseEnum.NO_FILES_ERROR.value,
                }
            )

            raise Exception(f"No files found for project_id:{project.project_id}")

        process_controller = ProcessController(project_id=project_id)

        no_records = 0
        no_files = 0

        chunk_model = await ChunkModel.create_instance(
            db_client=db_client
        )

        if do_reset == 1:
            collection_name = nlp_controller.create_collection_name(project_id=project.project_id)

            _ = await vectordb_client.delete_collection(collection_name=collection_name)

            _ = await chunk_model.delete_chunks_by_project_id(
                project_id=project.project_id
            )

        for asset_id, file_id in project_file_ids.items():

            file_content = process_controller.get_file_content(file_id=file_id)

            if file_content is None:
                logger.error(f"ERROR WHILE PROCESSING FILE: {file_id}")
                continue

            file_chunks = process_controller.process_file_content(
                file_content=file_content,
                file_id=file_id,
                chunk_size=chunk_size,
                overlap_size=overlap_size,
            )

            if file_chunks is None or len(file_chunks) == 0:

                logger.error(f"No chunks for file:{file_id}")
                pass

            file_chunks_record = [
                datachunk(
                    chunk_text=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    chunk_order=i + i,
                    chunk_project_id=project.project_id,
                    chunk_asset_id=asset_id

                )

                for i, chunk in enumerate(file_chunks)
            ]

            no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_record)
            no_files += 1

        task_instance.update_state(
            state="SUCCESS",
            metadata={
                "signal": ResponseEnum.PROCESSING_SUCCESS.value,
            }
        )

        return {
                "signal": ResponseEnum.PROCESSING_SUCCESS.value,
                "inserted_chunks": no_records,
                "processed_files": no_files
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












