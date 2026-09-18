from .decision import decide


def main():
    test_cases = [
        "My ₹3,500 order arrived damaged yesterday.",

        "I changed my mind about this unopened non-food product. "
        "It arrived 10 days ago.",

        "My parcel has still not arrived and it was dispatched "
        "9 days ago.",

        "I ordered strawberry but received chocolate 2 days ago.",

        "I want to return this.",
    ]

    for ticket in test_cases:
        print("\n" + "=" * 70)
        print("TICKET:")
        print(ticket)

        try:
            result = decide(ticket)

            print("\nDECISION:")
            print(result.model_dump_json(indent=2))

        except Exception as exc:
            print("\nERROR:")
            print(exc)


if __name__ == "__main__":
    main()