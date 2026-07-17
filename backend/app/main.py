from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import router as api_router
from fastapi.staticfiles import StaticFiles
from app.core.config import settings as app_settings
from app.core.database import init_db

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
@app.on_event("startup")
def on_startup():
    init_db()

app.mount("/media", StaticFiles(directory=app_settings.UPLOAD_DIR), name="media")

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} Backend API"}