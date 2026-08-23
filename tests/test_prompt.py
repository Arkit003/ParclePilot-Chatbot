from src.agent.prompt import SYSTEM_PROMPT


def test_prompt_contains_source_precedence():
    assert "Signed customer agreement" in SYSTEM_PROMPT
    assert "Current ParcelPilot support policy" in SYSTEM_PROMPT
    assert "Current ParcelPilot product documentation" in SYSTEM_PROMPT
    assert "Historical tickets / internal notes" in SYSTEM_PROMPT


def test_prompt_warns_about_deprecated_policy():
    assert "Deprecated policy documents" in SYSTEM_PROMPT


def test_prompt_requires_deterministic_tools():
    assert "check_cancellation" in SYSTEM_PROMPT
    assert "check_service_credit" in SYSTEM_PROMPT
    assert "get_sla_target" in SYSTEM_PROMPT


def test_prompt_requires_confirmation():
    assert "explicit user confirmation" in SYSTEM_PROMPT
    assert "preview_action" in SYSTEM_PROMPT


def test_prompt_requires_uncertainty():
    assert "do not guess" in SYSTEM_PROMPT.lower()