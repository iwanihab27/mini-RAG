from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from app.helpers.config import get_settings
from stores import LLMProviderFactory


load_dotenv(".env")

app = FastAPI(
    title=os.getenv("APP_NAME", "mini-rag"),
    version=os.getenv("APP_VERSION", "0.1"))


async def startup_db_client():
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient( settings.MONGODB_URL )
    app.db_client = app.mongo_conn[settings.MONGODB_DB]

    llm_provider_factory = LLMProviderFactory(settings)

    #generation client
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    #embedding client
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.generation_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                              embedding_size=settings.EMBEDDING_EMBEDDING_SIZE)

async def shutdown_db_client():
    app.mongo_conn.close()


app.router.lifespan.on_startup.append(startup_db_client)
app.router.lifespan.on_shutdown.append(shutdown_db_client)

app.include_router(base.BaseRouter)
app.include_router(data.DataRouter)

