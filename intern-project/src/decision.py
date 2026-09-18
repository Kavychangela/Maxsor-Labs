import json

from pydantic import BaseModel, Field
from google import genai

from .config import settings
from .retrieval import retrieve


class AIDecision(BaseModel):
    action: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    sources: list[str]


ALLOWED_ACTIONS = {
    "REQUEST_PHOTOS",
    "APPROVE_REFUND_OR_REPLACEMENT",
    "APPROVE_RETURN",
    "REJECT_OUTSIDE_WINDOW",
    "REJECT_OPENED_ITEM",
    "REJECT_FOOD_RETURN",
    "OPEN_SHIPPING_INVESTIGATION",
    "WAIT_AND_TRACK",
    "OFFER_REPLACEMENT_OR_REFUND",
    "CANCEL_AND_REFUND",
    "CANNOT_CANCEL_AFTER_DISPATCH",
    "REPLACE_CORRECT_ITEM",
    "APPROVE_REPLACEMENT",
    "REQUEST_DEFECT_EVIDENCE",
    "NEEDS_MORE_INFORMATION",
}


DECISION_PROMPT = """
You are an AI support-ticket decision assistant.

Your job is to decide the correct support action using ONLY the
provided policy context and the ticket information.

IMPORTANT RULES:

1. Do not invent policy rules.
2. Do not use general knowledge.
3. Do not assume missing information.
4. If information required by the policy is missing, return
   NEEDS_MORE_INFORMATION.
5. The action must be one of the allowed actions.
6. The reason must explain the decision using the supplied policy.
7. Sources must contain only policy filenames actually used.
8. Confidence must be between 0.0 and 1.0.
9. If the evidence is ambiguous or insufficient, prefer
   NEEDS_MORE_INFORMATION rather than guessing.

ALLOWED ACTIONS:

{allowed_actions}

SUPPORT TICKET:

{ticket}

RETRIEVED POLICY CONTEXT:

{context}

Return ONLY valid JSON with this structure:

{{
  "action": "ACTION_NAME",
  "confidence": 0.0,
  "reason": "Short explanation grounded in the policy.",
  "sources": ["policy_file.md"]
}}
"""


def build_context(results: list[dict]) -> str:
    """Convert retrieved chunks into LLM-readable context."""

    sections = []

    for result in results:
        sections.append(
            f"""
SOURCE: {result["source"]}
RELEVANCE: {result["score"]:.4f}

{result["text"]}
""".strip()
        )

    return "\n\n---\n\n".join(sections)


def decide(ticket: str, top_k: int = 4) -> AIDecision:
    """
    Retrieve relevant policies and ask Gemini
    to produce a structured decision.
    """

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    retrieved = retrieve(
        ticket,
        top_k=top_k,
    )

    if not retrieved:
        return AIDecision(
            action="NEEDS_MORE_INFORMATION",
            confidence=1.0,
            reason="No relevant policy information was retrieved.",
            sources=[],
        )

    context = build_context(retrieved)

    prompt = DECISION_PROMPT.format(
        allowed_actions="\n".join(
            f"- {action}"
            for action in sorted(ALLOWED_ACTIONS)
        ),
        ticket=ticket,
        context=context,
    )

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "temperature": 0,
            "thinking_level": "low",
        },
    )

    response_text = interaction.output_text

    if not response_text:
        raise RuntimeError("Gemini returned an empty response.")

    raw_text = response_text.strip()

    # Remove Markdown code fences if Gemini added them
    if raw_text.startswith("```"):
        raw_text = raw_text.removeprefix("```json").removeprefix("```").strip()

    if raw_text.endswith("```"):
        raw_text = raw_text.removesuffix("```").strip()

    try:
        raw_decision = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Gemini returned invalid JSON. Raw response: {response_text}"
        ) from exc

    decision = AIDecision.model_validate(
        raw_decision
    )

    if decision.action not in ALLOWED_ACTIONS:
        raise RuntimeError(
            f"Gemini returned unsupported action: "
            f"{decision.action}"
        )

    retrieved_sources = {
        result["source"]
        for result in retrieved
    }

    invalid_sources = set(
        decision.sources
    ) - retrieved_sources

    if invalid_sources:
        raise RuntimeError(
            "Gemini referenced sources that were "
            "not retrieved: "
            f"{invalid_sources}"
        )

    return decision