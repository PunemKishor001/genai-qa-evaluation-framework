from datetime import date
import re


CALLERS = {
    "atlas-employee-01": {
        "tenant": "Atlas",
        "role": "employee",
    },
    "atlas-contractor-01": {
        "tenant": "Atlas",
        "role": "contractor",
    },
    "boreal-employee-01": {
        "tenant": "Boreal",
        "role": "employee",
    },
}


def parse_date(value):
    return date.fromisoformat(value)


def get_caller(caller_id):
    return CALLERS.get(caller_id)


def check_caller_identity(recording, expected_status=401):
    caller_id = recording["request"].get("caller_id")
    valid = get_caller(caller_id) is not None
    actual_http = recording["observed"].get("http_status")

    if valid:
        return {
            "rule": "Caller identity validation",
            "expected": "Known caller",
            "observed": caller_id,
            "verdict": "PASS",
            "reason": "Caller ID exists in the supplied identity lookup.",
        }

    passed = actual_http == expected_status

    return {
        "rule": "Caller identity validation",
        "expected": {
            "caller": "Known caller ID",
            "http_status": expected_status,
        },
        "observed": {
            "caller": caller_id,
            "http_status": actual_http,
        },
        "verdict": "PASS" if passed else "FAIL",
        "reason": (
            "Unknown or missing caller is rejected with HTTP 401."
            if passed
            else "Unknown or missing caller was not rejected with HTTP 401."
        ),
    }


def check_request_date(recording):
    value = recording["request"].get("as_of")

    try:
        parse_date(value)
        valid = True
    except (TypeError, ValueError):
        valid = False

    actual_http = recording["observed"].get("http_status")

    if valid:
        return {
            "rule": "Request date validation",
            "expected": "Valid YYYY-MM-DD calendar date",
            "observed": value,
            "verdict": "PASS",
            "reason": "Request date is a valid calendar date.",
        }

    passed = actual_http == 400

    return {
        "rule": "Request date validation",
        "expected": {
            "valid_date": False,
            "http_status": 400,
        },
        "observed": {
            "value": value,
            "http_status": actual_http,
        },
        "verdict": "PASS" if passed else "FAIL",
        "reason": (
            "Invalid calendar date is rejected with HTTP 400."
            if passed
            else "Invalid calendar date was not rejected with HTTP 400."
        ),
    }


def get_eligible_policies(policies, caller_id, as_of):
    caller = get_caller(caller_id)

    if not caller:
        return []

    requested_date = parse_date(as_of)

    eligible = []

    for policy in policies.values():
        if policy["state"] != "Approved":
            continue

        if policy["tenant"] != caller["tenant"]:
            continue

        if policy["role"] != caller["role"]:
            continue

        start = parse_date(policy["effective_from"])
        end = parse_date(policy["effective_to"])

        if start <= requested_date < end:
            eligible.append(policy)

    return eligible


def check_http_status(recording, expected_status):
    actual = recording["observed"]["http_status"]

    return {
        "rule": "HTTP status",
        "expected": expected_status,
        "observed": actual,
        "verdict": "PASS" if actual == expected_status else "FAIL",
        "reason": (
            "HTTP status matches expected contract behavior."
            if actual == expected_status
            else "HTTP status does not match the contract."
        ),
    }


def check_business_status(recording, expected_status):
    actual = recording["observed"].get("status")

    return {
        "rule": "Business status",
        "expected": expected_status,
        "observed": actual,
        "verdict": "PASS" if actual == expected_status else "FAIL",
        "reason": (
            "Business status matches expected behavior."
            if actual == expected_status
            else "Business status does not match expected behavior."
        ),
    }


def check_response_contract(recording):
    observed = recording["observed"]
    status = observed.get("status")
    answer = observed.get("answer")
    citations = observed.get("citations", [])

    if status == "ANSWERED":
        passed = (
            isinstance(answer, str)
            and bool(answer.strip())
            and isinstance(citations, list)
            and len(citations) >= 1
        )

    elif status in {"INSUFFICIENT_EVIDENCE", "CONFLICT"}:
        passed = answer is None and citations == []

    else:
        return {
            "rule": "Response contract",
            "expected": "Known business response status",
            "observed": status,
            "verdict": "NOT_EVALUATED",
            "reason": "Response contract is not applicable to this status.",
        }

    return {
        "rule": "Response contract",
        "expected": (
            "ANSWERED: non-empty answer with citation(s); "
            "INSUFFICIENT_EVIDENCE/CONFLICT: null answer and empty citations"
        ),
        "observed": {
            "status": status,
            "answer": answer,
            "citations": citations,
        },
        "verdict": "PASS" if passed else "FAIL",
        "reason": (
            "Response shape matches the status contract."
            if passed
            else "Response shape does not match the status contract."
        ),
    }


def check_answer_contains_fact(recording, required_fact):
    answer = recording["observed"].get("answer") or ""

    normalized_answer = answer.lower()
    normalized_fact = required_fact.lower()

    passed = normalized_fact in normalized_answer

    return {
        "rule": "Required fact",
        "expected": required_fact,
        "observed": answer,
        "verdict": "PASS" if passed else "FAIL",
        "reason": (
            "Required fact is present."
            if passed
            else "Required fact is missing from the answer."
        ),
    }


def check_answer_contains_amount(recording, required_amount):
    return check_answer_contains_fact(recording, required_amount)


def check_no_prohibited_claims(recording):
    answer = recording["observed"].get("answer") or ""

    prohibited_phrases = [
        "claim is approved",
        "payment is guaranteed",
        "guarantee payment",
        "i approve",
        "claim approved",
    ]

    found = [
        phrase
        for phrase in prohibited_phrases
        if phrase in answer.lower()
    ]

    return {
        "rule": "No prohibited claims",
        "expected": "No unsupported approval/payment claims",
        "observed": found,
        "verdict": "PASS" if not found else "FAIL",
        "reason": (
            "No prohibited business claims detected."
            if not found
            else f"Unsupported claim(s) detected: {found}"
        ),
    }


def check_citations(recording, policies, eligible_ids=None):
    citations = recording["observed"].get("citations", [])

    if not citations:
        return {
            "rule": "Citation integrity",
            "expected": "At least one valid citation for ANSWERED",
            "observed": [],
            "verdict": "FAIL",
            "reason": "Answered response contains no citation.",
        }

    failures = []

    for citation in citations:
        chunk_id = citation.get("chunk_id")
        quote = citation.get("quote")

        if chunk_id not in policies:
            failures.append(f"Unknown chunk_id: {chunk_id}")
            continue

        if eligible_ids is not None and chunk_id not in eligible_ids:
            failures.append(
                f"{chunk_id}: citation references an ineligible policy"
            )

        actual_passage = policies[chunk_id]["passage"]

        if quote != actual_passage:
            failures.append(
                f"{chunk_id}: quote does not exactly match policy passage"
            )

    return {
        "rule": "Citation integrity",
        "expected": (
            "Citation references an eligible passage and quote exactly "
            "matches the policy passage"
        ),
        "observed": citations,
        "verdict": "PASS" if not failures else "FAIL",
        "reason": (
            "All citation quotations reference eligible policy text."
            if not failures
            else "; ".join(failures)
        ),
    }


def check_context_eligibility(recording, policies):
    request = recording["request"]

    try:
        eligible = get_eligible_policies(
            policies,
            request.get("caller_id"),
            request.get("as_of"),
        )
    except (TypeError, ValueError):
        return {
            "rule": "Generation context eligibility",
            "expected": "Not evaluated for invalid request",
            "observed": recording["trace"].get("model_context_ids", []),
            "verdict": "NOT_EVALUATED",
            "reason": "Request date is invalid.",
        }

    eligible_ids = {
        policy["chunk_id"]
        for policy in eligible
    }

    actual_ids = set(
        recording["trace"].get("model_context_ids", [])
    )

    unexpected = actual_ids - eligible_ids

    return {
        "rule": "Generation context eligibility",
        "expected": sorted(eligible_ids),
        "observed": sorted(actual_ids),
        "verdict": "PASS" if not unexpected else "FAIL",
        "reason": (
            "All generation context passages are eligible."
            if not unexpected
            else f"Ineligible context detected: {sorted(unexpected)}"
        ),
    }


def check_generation_attempts(recording, expected_attempts):
    actual = recording["trace"]["generation_attempts"]

    return {
        "rule": "Generation attempt count",
        "expected": expected_attempts,
        "observed": actual,
        "verdict": "PASS" if actual == expected_attempts else "FAIL",
        "reason": (
            "Generation attempt count matches expectation."
            if actual == expected_attempts
            else "Generation attempt count does not match expectation."
        ),
    }


def check_provider_behavior(recording, expected_provider_event):
    actual = recording["trace"]["provider_event"]

    return {
        "rule": "Provider event",
        "expected": expected_provider_event,
        "observed": actual,
        "verdict": "PASS" if actual == expected_provider_event else "FAIL",
        "reason": (
            "Provider event matches expected behavior."
            if actual == expected_provider_event
            else "Provider event does not match expected behavior."
        ),
    }


def check_provider_http_mapping(recording):
    provider_event = recording["trace"].get("provider_event")

    expected_map = {
        "timeout": 503,
        "unavailable": 503,
        "malformed": 502,
    }

    if provider_event not in expected_map:
        return {
            "rule": "Provider error HTTP mapping",
            "expected": "Not applicable",
            "observed": provider_event,
            "verdict": "NOT_EVALUATED",
            "reason": "No provider error event is recorded.",
        }

    expected_status = expected_map[provider_event]
    actual_status = recording["observed"].get("http_status")

    return {
        "rule": "Provider error HTTP mapping",
        "expected": expected_status,
        "observed": actual_status,
        "verdict": (
            "PASS"
            if actual_status == expected_status
            else "FAIL"
        ),
        "reason": (
            "Provider failure is mapped to the contract HTTP status."
            if actual_status == expected_status
            else "Provider failure is mapped to the wrong HTTP status."
        ),
    }


def check_no_generation_on_invalid_request(recording):
    trace = recording["trace"]

    passed = (
        trace["generation_attempts"] == 0
        and trace["provider_event"] == "not_called"
        and trace["model_context_ids"] == []
    )

    return {
        "rule": "Invalid request must not invoke generation",
        "expected": {
            "generation_attempts": 0,
            "provider_event": "not_called",
            "model_context_ids": [],
        },
        "observed": {
            "generation_attempts": trace["generation_attempts"],
            "provider_event": trace["provider_event"],
            "model_context_ids": trace["model_context_ids"],
        },
        "verdict": "PASS" if passed else "FAIL",
        "reason": (
            "No generation was invoked for invalid request."
            if passed
            else "Generation-related activity was recorded for invalid request."
        ),
    }


def question_matches_policy(question, passage):
    q = question.lower()
    p = passage.lower()

    subjects = [
        ("certification", "certification"),
        ("home-office", "home-office"),
        ("rail travel", "rail travel"),
        ("external training", "external training"),
        ("gym", "wellness"),
        ("wellness", "wellness"),
        ("balance", "balance"),
    ]

    for question_term, policy_term in subjects:
        if question_term in q and policy_term in p:
            return True

    return False


def get_relevant_policies(policies, question):
    return [
        policy
        for policy in policies
        if question_matches_policy(
            question,
            policy["passage"],
        )
    ]


def check_conflict_behavior(recording, eligible_policies):
    question = recording["request"].get("question", "")

    relevant = get_relevant_policies(
        eligible_policies,
        question,
    )

    if len(relevant) < 2:
        return {
            "rule": "Conflict handling",
            "expected": "Not applicable",
            "observed": "No multiple relevant policies",
            "verdict": "NOT_EVALUATED",
            "reason": (
                "Fewer than two simultaneously eligible policies "
                "address the requested subject."
            ),
        }

    passages = [
        policy["passage"]
        for policy in relevant
    ]

    contradictory = len(set(passages)) > 1

    if not contradictory:
        return {
            "rule": "Conflict handling",
            "expected": "No conflict",
            "observed": "Equivalent policies",
            "verdict": "NOT_EVALUATED",
            "reason": "Multiple relevant policies do not contradict each other.",
        }

    observed_status = recording["observed"].get("status")
    citations = recording["observed"].get("citations", [])

    cited_ids = {
        citation.get("chunk_id")
        for citation in citations
    }

    relevant_ids = {
        policy["chunk_id"]
        for policy in relevant
    }

    cites_relevant_policy = bool(
        cited_ids.intersection(relevant_ids)
    )

    passed = (
        observed_status == "CONFLICT"
        and recording["observed"].get("answer") is None
        and citations == []
    )

    # The contract says CONFLICT has null answer and empty citations.
    # Evidence showing disagreement is supplied by the underlying
    # applicable policy set, so we do not require citations in the
    # recorded conflict response itself.
    return {
        "rule": "Conflict handling",
        "expected": {
            "status": "CONFLICT",
            "answer": None,
            "citations": [],
        },
        "observed": {
            "status": observed_status,
            "answer": recording["observed"].get("answer"),
            "citations": citations,
        },
        "verdict": "PASS" if passed else "FAIL",
        "reason": (
            "Contradictory simultaneously applicable policies "
            "were not silently resolved."
            if passed
            else "Contradictory policies were silently resolved "
                 "or the CONFLICT response shape was invalid."
        ),
    }


def check_conflict_fixture_evidence(recording, policies):
    question = recording["request"].get("question", "")

    eligible = get_eligible_policies(
        policies,
        recording["request"].get("caller_id"),
        recording["request"].get("as_of"),
    )

    relevant = get_relevant_policies(
        eligible,
        question,
    )

    if len(relevant) < 2:
        return {
            "rule": "Conflict evidence",
            "expected": "At least two contradictory relevant policies",
            "observed": [p["chunk_id"] for p in relevant],
            "verdict": "NOT_EVALUATED",
            "reason": "No contradictory policy pair exists for this question.",
        }

    amounts = []

    for policy in relevant:
        match = re.search(
            r"INR\s*(\d+)",
            policy["passage"],
            re.IGNORECASE,
        )
        if match:
            amounts.append(int(match.group(1)))

    contradictory = len(set(amounts)) > 1

    return {
        "rule": "Conflict evidence",
        "expected": "Relevant policies contain contradictory values",
        "observed": [
            {
                "chunk_id": p["chunk_id"],
                "passage": p["passage"],
            }
            for p in relevant
        ],
        "verdict": "PASS" if contradictory else "FAIL",
        "reason": (
            "Relevant policies contain different supported values."
            if contradictory
            else "Relevant policies do not demonstrate a contradiction."
        ),
    }


def build_result(recording_id, checks):
    fail_count = sum(
        1
        for check in checks
        if check["verdict"] == "FAIL"
    )

    pass_count = sum(
        1
        for check in checks
        if check["verdict"] == "PASS"
    )

    overall = "FAIL" if fail_count else "PASS"

    return {
        "recording_id": recording_id,
        "overall_verdict": overall,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "checks": checks,
    }