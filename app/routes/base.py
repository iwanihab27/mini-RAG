from fastapi import APIRouter, FastAPI, Depends
import os
from app.helpers.config import get_settings, Settings
import logging
from time import sleep

logger = logging.getLogger('uvicorn.error')

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

@BaseRouter.get("/send_reports")
async def send_reports(app_settings: Settings = Depends(get_settings)):
    from app.tasks.mail_service import send_email_reports

    task = send_email_reports.delay(
        mail_wait_seconds=3,
    )

    return {
        "success": True,
        "task_id": task.id,
    }