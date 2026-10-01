import copy

from evaluator.assertions import (
    check_citations,
    check_no_prohibited_claims,
    check_context_eligibility
)

from evaluator.loader import load_policies


def test_valid_citation_is_accepted():

    policies = load_policies()

    recording = {
        "observed": {
            "citations": [
                {
                    "chunk_id": "P02",
                    "quote": policies["P02"]["passage"]
                }
            ]
        }
    }

    result = check_citations(
        recording,
        policies
    )

    assert result["verdict"] == "PASS"


def test_wrong_citation_quote_is_rejected():

    policies = load_policies()

    recording = {
        "observed": {
            "citations": [
                {
                    "chunk_id": "P02",
                    "quote": "The annual certification reimbursement limit is INR 35000."
                }
            ]
        }
    }

    result = check_citations(
        recording,
        policies
    )

    assert result["verdict"] == "FAIL"


def test_prohibited_payment_claim_is_rejected():

    recording = {
        "observed": {
            "answer": (
                "The limit is INR 25000. "
                "Your claim is approved and payment is guaranteed."
            )
        }
    }

    result = check_no_prohibited_claims(
        recording
    )

    assert result["verdict"] == "FAIL"


def test_meaning_preserving_answer_has_no_prohibited_claim():

    recording = {
        "observed": {
            "answer": (
                "The yearly certification reimbursement "
                "cap is INR 25,000."
            )
        }
    }

    result = check_no_prohibited_claims(
        recording
    )

    assert result["verdict"] == "PASS"


def test_ineligible_generation_context_is_rejected():

    policies = load_policies()

    recording = {
        "request": {
            "caller_id": "atlas-employee-01",
            "as_of": "2026-09-21"
        },
        "trace": {
            "model_context_ids": [
                "P02",
                "P06"
            ]
        }
    }

    result = check_context_eligibility(
        recording,
        policies
    )

    assert result["verdict"] == "FAIL"