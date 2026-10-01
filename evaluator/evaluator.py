from evaluator.assertions import (
    check_http_status,
    check_business_status,
    check_answer_contains_fact,
    check_no_prohibited_claims,
    check_citations,
    check_context_eligibility,
    check_generation_attempts,
    check_provider_behavior,
    check_provider_http_mapping,
    check_no_generation_on_invalid_request,
    check_conflict_behavior,
    check_response_contract,
    check_caller_identity,
    check_request_date,
    get_caller,
    get_eligible_policies,
    get_relevant_policies,
    parse_date,
)


def evaluate_recording(recording, policies):
    checks = []

    recording_id = recording["recording_id"]
    request = recording["request"]
    trace = recording["trace"]
    provider_event = trace.get("provider_event")

    # ---------------------------------------------------------
    # Provider failures
    # ---------------------------------------------------------

    if provider_event in {"timeout", "unavailable", "malformed"}:

        expected_http = {
            "timeout": 503,
            "unavailable": 503,
            "malformed": 502,
        }[provider_event]

        checks.append(
            check_http_status(
                recording,
                expected_http,
            )
        )

        checks.append(
            check_provider_behavior(
                recording,
                provider_event,
            )
        )

        checks.append(
            check_provider_http_mapping(
                recording,
            )
        )

        checks.append(
            check_generation_attempts(
                recording,
                1,
            )
        )

        return build_result(
            recording_id,
            checks,
        )

    # ---------------------------------------------------------
    # Caller validation
    # ---------------------------------------------------------

    caller_id = request.get("caller_id")

    if not get_caller(caller_id):

        checks.append(
            check_caller_identity(
                recording,
                401,
            )
        )

        checks.append(
            check_http_status(
                recording,
                401,
            )
        )

        checks.append(
            check_no_generation_on_invalid_request(
                recording,
            )
        )

        return build_result(
            recording_id,
            checks,
        )

    # ---------------------------------------------------------
    # Question validation
    # ---------------------------------------------------------

    question = request.get("question")

    if not isinstance(question, str) or not question.strip():

        checks.append(
            check_http_status(
                recording,
                400,
            )
        )

        checks.append(
            check_no_generation_on_invalid_request(
                recording,
            )
        )

        return build_result(
            recording_id,
            checks,
        )

    # ---------------------------------------------------------
    # Date validation
    # ---------------------------------------------------------

    try:
        parse_date(request.get("as_of"))
    except (TypeError, ValueError):

        checks.append(
            check_request_date(
                recording,
            )
        )

        checks.append(
            check_http_status(
                recording,
                400,
            )
        )

        checks.append(
            check_no_generation_on_invalid_request(
                recording,
            )
        )

        return build_result(
            recording_id,
            checks,
        )

    # ---------------------------------------------------------
    # Normal request
    # ---------------------------------------------------------

    checks.append(
        check_context_eligibility(
            recording,
            policies,
        )
    )

    eligible = get_eligible_policies(
        policies,
        caller_id,
        request["as_of"],
    )

    # ---------------------------------------------------------
    # Determine policies relevant to this question
    # ---------------------------------------------------------

    relevant = get_relevant_policies(
        eligible,
        question,
    )

    # ---------------------------------------------------------
    # Conflict
    # ---------------------------------------------------------

    conflict_check = check_conflict_behavior(
        recording,
        eligible,
    )

    checks.append(conflict_check)

    conflict_detected = (
        conflict_check["verdict"] != "NOT_EVALUATED"
    )

    if conflict_detected:

        checks.append(
            check_business_status(
                recording,
                "CONFLICT",
            )
        )

        checks.append(
            check_response_contract(
                recording,
            )
        )

        return build_result(
            recording_id,
            checks,
        )

    # ---------------------------------------------------------
    # Missing evidence
    # ---------------------------------------------------------

    if not relevant or is_missing_evidence_question(question):

        checks.append(
            check_business_status(
                recording,
                "INSUFFICIENT_EVIDENCE",
            )
        )

        checks.append(
            check_response_contract(
                recording,
            )
        )

        return build_result(
            recording_id,
            checks,
        )

    # ---------------------------------------------------------
    # Normal answer
    # ---------------------------------------------------------

    checks.append(
        check_business_status(
            recording,
            "ANSWERED",
        )
    )

    eligible_ids = {
        policy["chunk_id"]
        for policy in eligible
    }

    checks.append(
        check_citations(
            recording,
            policies,
            eligible_ids,
        )
    )

    checks.append(
        check_response_contract(
            recording,
        )
    )

    checks.append(
        check_no_prohibited_claims(
            recording,
        )
    )

    required_amount = find_expected_amount(
        question,
        relevant,
    )

    if required_amount:

        # IMPORTANT: append the result.
        checks.append(
            check_answer_contains_fact(
                recording,
                required_amount,
            )
        )

    return build_result(
        recording_id,
        checks,
    )


def is_missing_evidence_question(question):
    question = question.lower()

    keywords = [
        "gym membership",
        "wellness benefit",
        "remaining balance",
        "balance",
    ]

    return any(
        keyword in question
        for keyword in keywords
    )


def find_expected_amount(question, policies):
    question = question.lower()

    for policy in policies:

        passage = policy["passage"]

        if "certification reimbursement limit" in passage.lower():

            if "certification" in question:

                amount = extract_inr_amount(
                    passage,
                )

                if amount:
                    return amount

        if "home-office allowance" in passage.lower():

            if "home-office" in question:

                amount = extract_inr_amount(
                    passage,
                )

                if amount:
                    return amount

    return None


def extract_inr_amount(text):
    import re

    match = re.search(
        r"INR\s*(\d+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    value = int(match.group(1))

    return f"INR {value:,}"


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

    return {
        "recording_id": recording_id,
        "overall_verdict": (
            "FAIL"
            if fail_count
            else "PASS"
        ),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "checks": checks,
    }


def evaluate_all(recordings, policies):

    return [
        evaluate_recording(
            recording,
            policies,
        )
        for recording in recordings
    ]