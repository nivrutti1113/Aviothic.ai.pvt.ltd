# Aviothic AI Backend - Routes Package

from .predict import router as predict_router
from .auth import router as auth_router
from .reporting import router as reporting_router

__all__ = ["predict_router", "auth_router", "reporting_router"]