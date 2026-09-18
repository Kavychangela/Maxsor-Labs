import json
from pathlib import Path

from .decision import decide


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_CASES_PATH = PROJECT_ROOT / "sample_test_cases.json"


def load_test_cases():
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate():
    test_cases = load_test_cases()

    total = len(test_cases)
    correct = 0

    print("=" * 60)
    print("AI DECISION EVALUATION")
    print("=" * 60)

    for case in test_cases:

        case_id = case["case_id"]
        message = case["message"]
        expected = case["expected_action"]

        print(f"\n{case_id}")
        print(f"Ticket: {message}")
        print(f"Expected: {expected}")

        try:
            result = decide(message)

            predicted = result.action

            print(f"Predicted: {predicted}")

            if predicted == expected:
                print("Result: PASS")
                correct += 1
            else:
                print("Result: FAIL")

        except Exception as exc:
            print("Predicted: ERROR")
            print(f"Error: {exc}")
            print("Result: FAIL")

    accuracy = (correct / total * 100) if total else 0

    print("\n" + "=" * 60)
    print(f"Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    evaluate()