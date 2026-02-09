from fastapi import APIRouter, FastAPI, Depends
import os
from app.helpers.config import get_settings, Settings


BaseRouter = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@BaseRouter.get("/welcome")
async def welcome(app_settings: Settings = Depends(get_settings)):

    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    return {
        "app_name": app_name,
        "app_version": app_version,
    }
