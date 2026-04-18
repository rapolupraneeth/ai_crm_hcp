import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.settings import get_settings
from db.database import Base, engine
from models import hcp_model, interaction_model, session_state  # noqa: F401
from routes.chat import router as chat_router
from routes.interaction import router as interaction_router
from routes.upload import router as upload_router


settings = get_settings()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for now allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
def on_startup() -> None:
   Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(interaction_router, prefix=settings.api_prefix)
app.include_router(upload_router, prefix=settings.api_prefix)

# Serve the frontend static build if it exists
static_dir = Path("static")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
