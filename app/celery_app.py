from celery import Celery
from celery.schedules import crontab

from app.helpers.config import get_settings
from app.stores.LLMProviderFactory import LLMProviderFactory
from app.stores.vectordb.VectorDBProviderFactory import VectorDBProvider
from app.stores.LLM.Templates.Template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

settings = get_settings()

async def get_setup_utilits():
    settings = get_settings()

    postgres_conn = create_async_engine(
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
    )

    db_engine = postgres_conn

    db_client = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProvider(config=settings, db_client=db_client)

    #generation client
    generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    #embedding client
    embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                              embedding_size=settings.EMBEDDING_MODEL_SIZE)

    #vector db client
    vectordb_client = vectordb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)

    await vectordb_client.connect()

    template_parser = TemplateParser(
        language=settings.DEFAULT_LANGUAGE
    )

    return (db_engine, db_client, llm_provider_factory, vectordb_provider_factory,
            generation_client, embedding_client, vectordb_client, template_parser)

# create a celery app instance
celery_app = Celery(
    "minirag",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.file_processing",
        "app.tasks.data_indexing",
        "app.tasks.process_workflow",
        "app.tasks.maintenance",
    ]
)

# conf celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=[
        settings.CELERY_TASK_SERIALIZER
    ],

    # task safety late ack prevent that task gets lost when worker crash ( acknowledged only when finished)
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,

    # time limits to prevent hanging tasks
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,

    # result backend
    task_ignore_result=False,
    result_expires=3600,


    # worker settings
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,

    # connection settings for battery reliability
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    worker_cancel_long_running_tasks_on_connection_loss=True,

    task_routes={
        "app.tasks.file_processing.process_project_files": {"queue": "file_processing"},
        "app.tasks.data_indexing.index_data_content": {"queue": "data_indexing"},
        "app.tasks.process_workflow.process_and_push_workflow": {"queue": "process_workflow"},
        "app.tasks,maintenance.clean_celery_executions_table": {"queue": "default"},# bec it runs in the background
    },

    beat_schedule = {
        'cleanup-old-task-records': {
            'task': 'app.tasks,maintenance.clean_celery_executions_table',

            'schedule': 86400,

            'args': ()

        }
    },

    timezone='UTC',

)

celery_app.conf.task_default_queue = "default"  # like a lane for tasks