"""App-state dependencies: provide services from request.app.state to routers."""
from fastapi import Request

from services.activity_service import ActivityService


def get_intent_detector(request: Request):
    return request.app.state.intent_detector


def get_brevo_service(request: Request):
    return request.app.state.brevo_service


def get_db_service(request: Request):
    return request.app.state.db_service


def get_email_worker(request: Request):
    return request.app.state.email_worker


def get_activity_service(request: Request) -> ActivityService:
    return request.app.state.activity_service
