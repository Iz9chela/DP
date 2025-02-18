from backend.services.routers import prompt_evaluator_router

import uvicorn
import logging
from fastapi import FastAPI
import motor.motor_asyncio
from backend.services.settings import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)

async def lifespan(app: FastAPI):
    # Startup: initialize Motor client and attach to app.state
    app.state.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    app.state.mongo_db = app.state.mongo_client[DB_NAME]
    logger.info("Connected to MongoDB at %s, using DB: %s", MONGO_URI, DB_NAME)
    yield  # Application runs while yielding
    # Shutdown: close the Motor client
    app.state.mongo_client.close()
    logger.info("MongoDB client closed.")
app = FastAPI(
    title="Prompt Evaluator API",
    description="API for evaluating prompts using AI and storing results in MongoDB",
    version="1.0.0"
)

app.include_router(prompt_evaluator_router.router, prefix="/evaluations", tags=["Evaluations"])

if __name__ == "__main__":
    uvicorn.run("backend.services.main:app", host="127.0.0.1", port=8000)
