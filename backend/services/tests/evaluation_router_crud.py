from fastapi.testclient import TestClient
from backend.services.main import app

client = TestClient(app)


def test_create_and_get_evaluation():
    post_data = {
        "prompt": "Test prompt for API integration",
        "evaluation_method": "human",
        "model": "gpt-3.5-turbo",
        "parsed_result": {"prompt_rating": 8, "reasons": ["Well-defined", "Clear instructions"]}
    }
    response = client.post("/evaluations/", json=post_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "id" in data, "Response should include an 'id' field"
    # Optionally, verify that '_id' is not present
    assert "_id" not in data, "Response should not include '_id' field"

    eval_id = data["id"]
    get_response = client.get(f"/evaluations/{eval_id}")
    assert get_response.status_code == 200, get_response.text
    get_data = get_response.json()
    assert get_data["prompt"] == post_data["prompt"]


def test_list_evaluations():
    response = client.get("/evaluations/?limit=5")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


def test_update_evaluation():
    post_data = {
        "prompt": "Prompt to update",
        "evaluation_method": "llm",
        "model": "gpt-3.5-turbo",
        "parsed_result": {"prompt_rating": 5, "reasons": ["Needs improvement"]}
    }
    post_resp = client.post("/evaluations/", json=post_data)
    assert post_resp.status_code == 200, post_resp.text
    eval_id = post_resp.json()["id"]

    update_data = {"parsed_result": {"prompt_rating": 9, "reasons": ["After update"]}}
    put_resp = client.put(f"/evaluations/{eval_id}", json=update_data)
    assert put_resp.status_code == 200, put_resp.text
    updated = put_resp.json()
    assert updated["parsed_result"]["prompt_rating"] == 9


def test_delete_evaluation():
    post_data = {
        "prompt": "Prompt to delete",
        "evaluation_method": "human",
        "model": "gpt-3.5-turbo",
        "parsed_result": {"prompt_rating": 6, "reasons": ["Delete me"]}
    }
    post_resp = client.post("/evaluations/", json=post_data)
    assert post_resp.status_code == 200, post_resp.text
    eval_id = post_resp.json()["id"]

    del_resp = client.delete(f"/evaluations/{eval_id}")
    assert del_resp.status_code == 200, del_resp.text

    get_resp = client.get(f"/evaluations/{eval_id}")
    assert get_resp.status_code == 404, "Deleted evaluation should not be retrievable"
