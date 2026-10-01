# Test Inventory

| ID | Area | Scenario | Priority |
|---|---|---|---|
| T01 | Response Contract | Valid answered response | High |
| T02 | Authorization | Contractor receives contractor policy | Critical |
| T03 | Effective Date | Boundary date 2026-06-01 | Critical |
| T04 | Conflict | Two contradictory policies apply | Critical |
| T05 | Missing Evidence | Unknown wellness/gym policy | High |
| T06 | Citation | Citation quote must match source | Critical |
| T07 | Provider Error | Provider timeout | Critical |
| T08 | Generation Context | Ineligible tenant policy must not be sent | Critical |
| T09 | Prompt Injection | Request text cannot change caller identity | Critical |
| T10 | Prohibited Claims | Cannot approve claims or guarantee payment | Critical |
| T11 | Wording Variation | Meaning-preserving answer accepted | Medium |
| T12 | Validation | Blank question | High |
| T13 | Validation | Missing question | High |
| T14 | Validation | Missing as_of | High |
| T15 | Validation | Invalid calendar date | High |
| T16 | Authentication | Unknown caller | Critical |
| T17 | Policy Eligibility | Boreal employee certification policy | High |
| T18 | Policy Eligibility | Atlas contractor certification policy | High |
| T19 | Evidence | Remaining reimbursement balance | High |
| T20 | Action Boundary | Claim approval request | Critical |

## Check Method

Checks are implemented as reusable Python assertions.

The evaluator checks:

- HTTP response behavior
- Business status
- Required facts
- Prohibited claims
- Citation integrity
- Policy eligibility
- Generation context
- Provider behavior
- Generation attempts
- Invalid-request behavior
- Conflict handling

## Execution Status

The twelve supplied recordings are evaluated from their recorded evidence.

The additional tests are designed cases and are marked separately from executed recording observations.