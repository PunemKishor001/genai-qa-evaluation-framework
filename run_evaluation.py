import json

from evaluator.loader import (
    load_policies,
    load_recordings
)

from evaluator.evaluator import evaluate_all


def main():

    policies = load_policies()
    recordings = load_recordings()

    results = evaluate_all(
        recordings,
        policies
    )

    report = {
        "assessment": "Marlabs GenAI QA Candidate Assessment",
        "evaluation_mode": "offline_recording_evaluation",
        "total_recordings": len(results),
        "results": results
    }

    with open(
        "reports/evaluation_report.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("=" * 70)
    print("MARLABS GENAI QA EVALUATION")
    print("=" * 70)

    for result in results:

        print(
            f"Recording {result['recording_id']}: "
            f"{result['overall_verdict']} "
            f"(PASS={result['pass_count']}, "
            f"FAIL={result['fail_count']})"
        )

    print("=" * 70)
    print(
        "Report written to: "
        "reports/evaluation_report.json"
    )


if __name__ == "__main__":
    main()