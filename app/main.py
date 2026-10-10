import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import health, paystack_hook, telegram_hook, verify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)
logger = logging.getLogger("sga")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Sales Growth Academy backend (env=%s)", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Sales Growth Academy",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# API + webhook routers
app.include_router(health.router)
app.include_router(verify.router)
app.include_router(paystack_hook.router)
app.include_router(telegram_hook.router)


# HTML pages
@app.get("/")
async def index() -> FileResponse | JSONResponse:
    path = TEMPLATES_DIR / "index.html"
    if path.exists():
        return FileResponse(path)
    return JSONResponse({"status": "ok", "message": "Sales Growth Academy backend"})


@app.get("/success")
async def success() -> FileResponse | JSONResponse:
    path = TEMPLATES_DIR / "success.html"
    if path.exists():
        return FileResponse(path)
    return JSONResponse({"status": "ok", "message": "Success page not yet configured"})
