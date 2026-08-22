from src.tools.actions import (
    execute_action,
    preview_action,
)
from src.schemas.actions_schema import (
    ExecuteActionInput,
    PreviewActionInput,
)


def test_preview_creates_pending_action():

    result = preview_action(
        PreviewActionInput(
            action_type="escalation",
            account_id="ACCT-001",
            reason="P1 incident requires human review.",
            ticket_id="TKT-450",
        )
    )

    assert result.status == "PENDING"
    assert result.confirmation_id
    assert result.requires_manager_approval is False


def test_execute_requires_confirmation():

    preview = preview_action(
        PreviewActionInput(
            action_type="escalation",
            account_id="ACCT-001",
            reason="Test escalation.",
        )
    )

    result = execute_action(
        ExecuteActionInput(
            confirmation_id=(
                preview.confirmation_id
            ),
            confirmed=False,
        ),
        acting_role="support_agent",
        acting_user_id="user-001",
    )

    assert result.status == "CANCELLED"


def test_support_agent_can_execute_under_threshold():

    preview = preview_action(
        PreviewActionInput(
            action_type="ticket_update",
            account_id="ACCT-001",
            reason="Update ticket.",
            amount_inr=500,
        )
    )

    result = execute_action(
        ExecuteActionInput(
            confirmation_id=(
                preview.confirmation_id
            ),
            confirmed=True,
        ),
        acting_role="support_agent",
        acting_user_id="user-001",
    )

    assert result.status == "EXECUTED"


def test_over_1000_requires_manager():

    preview = preview_action(
        PreviewActionInput(
            action_type="ticket_update",
            account_id="ACCT-001",
            reason="Large credit adjustment.",
            amount_inr=1500,
        )
    )

    try:
        execute_action(
            ExecuteActionInput(
                confirmation_id=(
                    preview.confirmation_id
                ),
                confirmed=True,
            ),
            acting_role="support_agent",
            acting_user_id="user-001",
        )

        assert False, (
            "Expected manager approval error."
        )

    except PermissionError as exc:
        assert "manager" in str(exc).lower()


def test_manager_can_execute_over_1000():

    preview = preview_action(
        PreviewActionInput(
            action_type="ticket_update",
            account_id="ACCT-001",
            reason="Large credit adjustment.",
            amount_inr=1500,
        )
    )

    result = execute_action(
        ExecuteActionInput(
            confirmation_id=(
                preview.confirmation_id
            ),
            confirmed=True,
        ),
        acting_role="manager",
        acting_user_id="manager-001",
    )

    assert result.status == "EXECUTED"