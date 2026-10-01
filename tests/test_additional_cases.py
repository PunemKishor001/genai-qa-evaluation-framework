from evaluator.assertions import (
    check_conflict_fixture_evidence,
    check_answer_contains_fact,
    check_citations,
)

from evaluator.evaluator import evaluate_recording
from evaluator.loader import load_policies


POLICIES = load_policies()

from evaluator.evaluator import evaluate_recording
from evaluator.loader import load_policies


POLICIES = load_policies()


def base_recording():
    return {
        "recording_id": "ADDITIONAL",
        "request": {
            "caller_id": "atlas-employee-01",
            "as_of": "2026-09-21",
            "question": "What is my annual certification reimbursement limit?",
        },
        "observed": {
            "http_status": 200,
            "status": "ANSWERED",
            "answer": "Your annual certification limit is INR 25,000.",
            "citations": [
                {
                    "chunk_id": "P02",
                    "quote": (
                        "The annual certification reimbursement limit "
                        "for employees is INR 25000."
                    ),
                }
            ],
        },
        "trace": {
            "model_context_ids": ["P02"],
            "generation_attempts": 1,
            "provider_event": "success",
        },
    }


def test_A01_unknown_caller_is_rejected():
    recording = base_recording()

    recording["request"]["caller_id"] = "unknown-user"
    recording["observed"]["http_status"] = 401
    recording["observed"]["status"] = None
    recording["observed"]["answer"] = None
    recording["observed"]["citations"] = []
    recording["trace"] = {
        "model_context_ids": [],
        "generation_attempts": 0,
        "provider_event": "not_called",
    }

    result = evaluate_recording(
        recording,
        POLICIES,
    )

    assert result["overall_verdict"] == "PASS"


def test_A02_missing_caller_is_rejected():
    recording = base_recording()

    recording["request"]["caller_id"] = None
    recording["observed"]["http_status"] = 401
    recording["observed"]["status"] = None
    recording["observed"]["answer"] = None
    recording["observed"]["citations"] = []
    recording["trace"] = {
        "model_context_ids": [],
        "generation_attempts": 0,
        "provider_event": "not_called",
    }

    result = evaluate_recording(
        recording,
        POLICIES,
    )

    assert result["overall_verdict"] == "PASS"


def test_A03_invalid_date_is_rejected():
    recording = base_recording()

    recording["request"]["as_of"] = "2026-02-30"
    recording["observed"]["http_status"] = 400
    recording["observed"]["status"] = None
    recording["observed"]["answer"] = None
    recording["observed"]["citations"] = []
    recording["trace"] = {
        "model_context_ids": [],
        "generation_attempts": 0,
        "provider_event": "not_called",
    }

    result = evaluate_recording(
        recording,
        POLICIES,
    )

    assert result["overall_verdict"] == "PASS"


def test_A04_malformed_provider_output_maps_to_502():
    recording = base_recording()

    recording["observed"]["http_status"] = 502
    recording["observed"]["status"] = None
    recording["observed"]["answer"] = None
    recording["observed"]["citations"] = []
    recording["trace"]["provider_event"] = "malformed"

    result = evaluate_recording(
        recording,
        POLICIES,
    )

    assert result["overall_verdict"] == "PASS"


def test_A05_conflicting_policies_require_conflict_status():
    recording = base_recording()

    recording["request"]["question"] = (
        "What is my annual home-office allowance?"
    )

    recording["observed"] = {
        "http_status": 200,
        "status": "CONFLICT",
        "answer": None,
        "citations": [],
    }

    recording["trace"]["model_context_ids"] = [
        "P07",
        "P08",
    ]

    result = evaluate_recording(
        recording,
        POLICIES,
    )

    assert result["overall_verdict"] == "PASS"


def test_A06_conflict_evidence_contains_two_different_values():
    recording = base_recording()

    recording["request"]["question"] = (
        "What is my annual home-office allowance?"
    )

    result = check_conflict_fixture_evidence(
        recording,
        POLICIES,
    )

    assert result["verdict"] == "PASS"


def test_A07_meaning_preserving_amount_is_accepted():
    recording = base_recording()

    recording["observed"]["answer"] = (
        "The yearly certification reimbursement ceiling "
        "for an employee is 25,000 Indian rupees."
    )

    result = check_answer_contains_fact(
        recording,
        "25,000 Indian rupees",
    )

    assert result["verdict"] == "PASS"


def test_A08_wrong_citation_quote_is_rejected():
    recording = base_recording()

    recording["observed"]["citations"][0]["quote"] = (
        "The annual certification reimbursement limit "
        "for employees is INR 35000."
    )

    result = check_citations(
        recording,
        POLICIES,
        {"P02"},
    )

    assert result["verdict"] == "FAIL"