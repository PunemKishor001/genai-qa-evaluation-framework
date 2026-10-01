import json
from pathlib import Path

from evaluator.assertions import (
    check_answer_contains_fact,
    check_citations,
    check_no_prohibited_claims,
)


FIXTURE_DIR = Path("tests/fixtures")


def load_fixture(name):
    with open(
        FIXTURE_DIR / name,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ---------------------------------------------------------
# Candidate-created faulty variants
# ---------------------------------------------------------


def test_faulty_wrong_amount_is_detected():
    recording = load_fixture(
        "faulty_wrong_amount.json"
    )

    result = check_answer_contains_fact(
        recording,
        "INR 25,000",
    )

    assert result["verdict"] == "FAIL"


def test_faulty_wrong_citation_is_detected():
    recording = load_fixture(
        "faulty_wrong_citation.json"
    )

    policies = {
        "P02": {
            "passage": (
                "The annual certification reimbursement limit "
                "for employees is INR 25000."
            )
        }
    }

    result = check_citations(
        recording,
        policies,
        {"P02"},
    )

    assert result["verdict"] == "FAIL"


def test_faulty_prohibited_claim_is_detected():
    recording = load_fixture(
        "faulty_prohibited_claim.json"
    )

    result = check_no_prohibited_claims(
        recording
    )

    assert result["verdict"] == "FAIL"


# ---------------------------------------------------------
# Candidate-created meaning-preserving variants
# ---------------------------------------------------------


def test_meaning_preserving_amount_variant_is_accepted():
    recording = load_fixture(
        "valid_amount_variant.json"
    )

    result = check_answer_contains_fact(
        recording,
        "25,000 Indian rupees",
    )

    assert result["verdict"] == "PASS"


def test_meaning_preserving_wording_variant_is_accepted():
    recording = load_fixture(
        "valid_wording_variant.json"
    )

    result = check_answer_contains_fact(
        recording,
        "INR 25,000",
    )

    assert result["verdict"] == "PASS"