import logging
from backend.services.db import init_db, get_db
from backend.services.routers.prompt_evaluation_router import (
    create_prompt_evaluation,
    get_prompt_evaluation,
    list_prompt_evaluations,
    update_prompt_evaluation,
    delete_prompt_evaluation,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_create_and_get():
    db = get_db()
    data = {
        "prompt": "Test prompt for CRUD operations.",
        "evaluation_method": "human",
        "model": "gpt-3.5-turbo",
        "parsed_result": {"prompt_rating": 7, "reasons": ["Initial test reason"]},
    }
    created_record = create_prompt_evaluation(data)
    record_id = created_record.get("id")
    assert record_id is not None
    retrieved_record = get_prompt_evaluation(record_id)
    assert retrieved_record is not None
    assert retrieved_record["prompt"] == "Test prompt for CRUD operations."

def test_list():
    db = get_db()
    records = list_prompt_evaluations(limit=5)
    assert isinstance(records, list)

def test_update():
    db = get_db()
    data = {
        "prompt": "Prompt to update",
        "evaluation_method": "llm",
        "model": "gpt-3.5-turbo",
        "parsed_result": {"prompt_rating": 5, "reasons": ["Before update"]},
    }
    created = create_prompt_evaluation(data)
    record_id = created.get("id")
    updated_data = {"parsed_result": {"prompt_rating": 8, "reasons": ["After update"]}}
    updated_record = update_prompt_evaluation(record_id, updated_data)
    assert updated_record is not None
    assert updated_record["parsed_result"]["prompt_rating"] == 8

def test_delete():
    db = get_db()
    data = {
        "prompt": "Prompt to delete",
        "evaluation_method": "human",
        "model": "gpt-3.5-turbo",
        "parsed_result": {"prompt_rating": 6, "reasons": ["Delete test"]},
    }
    created = create_prompt_evaluation(data)
    record_id = created.get("id")
    success = delete_prompt_evaluation(record_id)
    assert success is True
    deleted_record = get_prompt_evaluation(record_id)
    assert deleted_record is None

if __name__ == "__main__":
    init_db()
    test_create_and_get()
    test_list()
    test_update()
    test_delete()
    logger.info("All CRUD tests passed.")