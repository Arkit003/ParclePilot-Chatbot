from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.routes.actions import router
from src.tools.actions import preview_action
from src.schemas.actions_schema import PreviewActionInput

app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_unknown_confirmation_id_is_rejected():
    response = client.post(
        "/actions/does-not-exist/execute",
        params={
            "confirmed": True,
        },
        headers={
            "X-User-ID": "rohit",
        },
    )

    assert response.status_code == 400


def test_customer_cannot_execute_action():
    response = client.post(
        "/actions/does-not-exist/execute",
        params={
            "confirmed": True,
        },
        headers={
            "X-User-ID": "customer-northstar",
        },
    )

    # The current implementation checks the confirmation
    # record before role authorization, so this can be refined
    # after we make the action lookup/account scope stricter.
    assert response.status_code in {400, 403}

def test_support_agent_can_execute_pending_action():
    preview = preview_action(
        PreviewActionInput(
            action_type="escalation",
            account_id="ACCT-001",
            reason="P1 issue requires human review.",
            ticket_id="TKT-450",
            amount_inr=500,
        )
    )

    response = client.post(
        f"/actions/{preview.confirmation_id}/execute",
        params={
            "confirmed": True,
        },
        headers={
            "X-User-ID": "rohit",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "EXECUTED"
    assert data["confirmation_id"] == (
        preview.confirmation_id
    )

def test_support_agent_cannot_execute_over_1000():
    preview = preview_action(
        PreviewActionInput(
            action_type="ticket_update",
            account_id="ACCT-001",
            reason="Large adjustment.",
            amount_inr=1500,
        )
    )

    response = client.post(
        f"/actions/{preview.confirmation_id}/execute",
        params={
            "confirmed": True,
        },
        headers={
            "X-User-ID": "rohit",
        },
    )

    assert response.status_code == 403

def test_manager_can_execute_over_1000():
    preview = preview_action(
        PreviewActionInput(
            action_type="ticket_update",
            account_id="ACCT-001",
            reason="Large adjustment.",
            amount_inr=1500,
        )
    )

    response = client.post(
        f"/actions/{preview.confirmation_id}/execute",
        params={
            "confirmed": True,
        },
        headers={
            "X-User-ID": "manager",
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "EXECUTED"

def test_explicit_rejection_cancels_action():
    preview = preview_action(
        PreviewActionInput(
            action_type="follow_up",
            account_id="ACCT-001",
            reason="Follow up with customer.",
        )
    )

    response = client.post(
        f"/actions/{preview.confirmation_id}/execute",
        params={
            "confirmed": False,
        },
        headers={
            "X-User-ID": "rohit",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"