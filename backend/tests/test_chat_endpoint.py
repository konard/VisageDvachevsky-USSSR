"""End-to-end test for the leader chat HTTP endpoint."""
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Run the test against the lightweight legacy Flask app.
import app as flask_app_module  # noqa: E402
from chat_service import OllamaUnavailableError  # noqa: E402


@pytest.fixture()
def client():
    flask_app_module.app.config['TESTING'] = True
    flask_app_module.db.initialize_data()
    with flask_app_module.app.test_client() as c:
        yield c


def test_chat_endpoint_returns_reply(client):
    fake_result = {
        "reply": "Я Ленин, рад вас приветствовать.",
        "history": [
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Я Ленин, рад вас приветствовать."},
        ],
        "model": "llama3.1:8b",
        "off_topic": False,
    }
    with patch.object(flask_app_module.chat_service, "chat", return_value=fake_result) as mocked:
        resp = client.post("/api/leaders/1/chat", json={"message": "Привет"})

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["reply"].startswith("Я Ленин")
    assert data["leader"]["id"] == 1
    assert data["off_topic"] is False
    assert mocked.called


def test_chat_endpoint_validates_empty_message(client):
    resp = client.post("/api/leaders/1/chat", json={"message": "   "})
    assert resp.status_code == 400


def test_chat_endpoint_handles_missing_leader(client):
    resp = client.post("/api/leaders/999/chat", json={"message": "test"})
    assert resp.status_code == 404


def test_chat_endpoint_reports_503_when_ollama_down(client):
    with patch.object(
        flask_app_module.chat_service,
        "chat",
        side_effect=OllamaUnavailableError("offline"),
    ):
        resp = client.post("/api/leaders/1/chat", json={"message": "Что вы думаете?"})
    assert resp.status_code == 503
    body = resp.get_json()
    assert body["available"] is False
    assert "offline" in body["error"]


def test_chat_health_endpoint(client):
    with patch.object(
        flask_app_module.chat_service,
        "health",
        return_value={"available": True, "model": "x", "models": ["x"], "model_present": True, "base_url": "u"},
    ):
        resp = client.get("/api/chat/health")
    assert resp.status_code == 200
    assert resp.get_json()["available"] is True
