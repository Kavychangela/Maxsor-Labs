import pytest

from src.retrieval import retrieve


@pytest.mark.parametrize(
    "query,expected_source",
    [
        (
            "My package is damaged and cost 2500 rupees.",
            "damaged_goods.md",
        ),
        (
            "I received the wrong flavour.",
            "wrong_item.md",
        ),
        (
            "My order is 9 days late.",
            "shipping.md",
        ),
        (
            "I received a defective product.",
            "defective_products.md",
        ),
        (
            "I want to cancel before dispatch.",
            "cancellations.md",
        ),
        (
            "Can I return an unopened non-food product?",
            "returns.md",
        ),
    ],
)
def test_relevant_policy_is_retrieved(
    query,
    expected_source,
):
    results = retrieve(
        query,
        top_k=4,
    )

    sources = [
        result["source"]
        for result in results
    ]

    assert expected_source in sources