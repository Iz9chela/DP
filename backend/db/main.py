from starlette.middleware.cors import CORSMiddleware

from backend.db.routers import prompt_evaluator_router
from backend.db.routers.user_router import router as user_router

import uvicorn
import logging
from fastapi import FastAPI
import motor.motor_asyncio
from backend.db.settings import MONGO_URI, DB_NAME
from backend.db.routers.optimization_prompt_router import router as optimized_router
from backend.utils.http_error_handler import handle_generic_exception

logger = logging.getLogger(__name__)

async def lifespan(app: FastAPI):
    """
        Ensures MongoDB connection is established at startup and closed at shutdown.
    """
    try:
        app.state.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        app.state.mongo_db = app.state.mongo_client[DB_NAME]
        logger.info("Connected to MongoDB at %s", MONGO_URI)
        yield
    except Exception as e:
        handle_generic_exception(e)

    finally:
        app.state.mongo_client.close()
        logger.info("MongoDB connection closed.")

app = FastAPI(
    title="Prompt Optimization API",
    description="API for evaluating, optimization and testing prompts using AI and storing results in MongoDB",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(prompt_evaluator_router.router, prefix="/evaluations", tags=["Evaluations"])
app.include_router(optimized_router, prefix="/optimizations", tags=["Optimized Prompts"])

if __name__ == "__main__":
    uvicorn.run("backend.db.main:app", host="127.0.0.1", port=8000)
