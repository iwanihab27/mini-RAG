from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from app.helpers.config import get_settings


load_dotenv(".env")

app = FastAPI(
    title=os.getenv("APP_NAME", "mini-rag"),
    version=os.getenv("APP_VERSION", "0.1"))


@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient( settings.MONGODB_URL )
    app.db_client = app.mongo_conn[settings.MONGODB_DB]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_conn.close()


app.include_router(base.BaseRouter)
app.include_router(data.DataRouter)

