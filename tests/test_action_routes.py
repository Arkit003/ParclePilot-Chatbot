from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.routes.actions import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_execute_unknown_confirmation_id():
    response = client.post(
        "/actions/does-not-exist/execute",
        params={
            "confirmed": True,
        },
    )

    assert response.status_code == 400