import pytest

from src.decision import AIDecision, ALLOWED_ACTIONS


def test_decision_schema_valid():
    decision = AIDecision(
        action="REQUEST_PHOTOS",
        confidence=0.95,
        reason="Photos are required for damaged orders above ₹2,000.",
        sources=["damaged_goods.md"],
    )

    assert decision.action == "REQUEST_PHOTOS"
    assert 0.0 <= decision.confidence <= 1.0
    assert decision.sources == ["damaged_goods.md"]


def test_decision_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        AIDecision(
            action="REQUEST_PHOTOS",
            confidence=1.5,
            reason="Invalid confidence.",
            sources=[],
        )


def test_allowed_actions_are_defined():
    assert "REQUEST_PHOTOS" in ALLOWED_ACTIONS
    assert "APPROVE_RETURN" in ALLOWED_ACTIONS
    assert "NEEDS_MORE_INFORMATION" in ALLOWED_ACTIONS