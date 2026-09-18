from .retrieval import retrieve


def main():
    queries = [
        "My package is damaged and the order cost 2500 rupees.",
        "I want to cancel my order before it is shipped.",
        "I received the wrong flavour.",
        "My package is 9 days late.",
        "I received a defective product.",
    ]

    for query in queries:
        print("\n" + "=" * 70)
        print("QUERY:")
        print(query)

        results = retrieve(
            query,
            top_k=3,
        )

        print("\nRETRIEVED:")

        for result in results:
            print(
                f"\nSource: {result['source']}"
            )
            print(
                f"Score: {result['score']:.4f}"
            )
            print(
                f"Text: {result['text'][:300]}"
            )


if __name__ == "__main__":
    main()