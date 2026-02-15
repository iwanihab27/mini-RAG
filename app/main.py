from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.routes import base, data, nlp
from motor.motor_asyncio import AsyncIOMotorClient
from app.helpers.config import get_settings
from app.stores.LLMProviderFactory import LLMProviderFactory
from app.stores.vectordb.VectorDBProviderFactory import VectorDBProvider


load_dotenv(".env")

app = FastAPI(
    title=os.getenv("APP_NAME", "mini-rag"),
    version=os.getenv("APP_VERSION", "0.1"))


async def startup_span():
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient( settings.MONGODB_URL )
    app.db_client = app.mongo_conn[settings.MONGODB_DB]

    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProvider(settings)

    #generation client
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    #embedding client
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.generation_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                              embedding_size=settings.EMBEDDING_MODEL_SIZE)

    #vector db client
    app.vectordb_client = vectordb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)

    app.vectordb_client.connect()


async def shutdown_span():
    app.mongo_conn.close()
    app.vectordb_client.disconnect()




app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

app.include_router(base.BaseRouter)
app.include_router(data.DataRouter)
app.include_router(nlp.NLPRouter)

