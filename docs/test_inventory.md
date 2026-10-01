\# Test Inventory



\## Supplied Recordings



| ID | Risk Area | Expected |

|---|---|---|

| 01 | Basic policy retrieval | ANSWERED |

| 02 | Role isolation | ANSWERED but recorded behavior defective |

| 03 | Effective-date selection | ANSWERED but recorded behavior defective |

| 04 | Policy conflict | CONFLICT |

| 05 | Missing evidence | INSUFFICIENT\_EVIDENCE |

| 06 | Citation integrity | ANSWERED with invalid citation evidence |

| 07 | Provider timeout | 503 |

| 08 | Tenant isolation | ANSWERED with invalid context |

| 09 | Prompt injection / identity isolation | ANSWERED using caller identity |

| 10 | Unsupported business claim | ANSWERED without unsupported claims |

| 11 | Meaning-preserving wording | ANSWERED |

| 12 | Invalid request | 400 |



\## Additional Designed Cases



| ID | Scenario | Expected |

|---|---|---|

| A01 | Unknown caller | HTTP 401 |

| A02 | Missing caller ID | HTTP 401 |

| A03 | Invalid date | HTTP 400 |

| A04 | Malformed provider output | HTTP 502 |

| A05 | CONFLICT with non-null answer | FAIL |

| A06 | CONFLICT without disagreement evidence | FAIL |

| A07 | Meaning-preserving monetary wording | PASS |

| A08 | Correct citation ID with incorrect quote | FAIL |



\## Priority



P0:

\- Tenant/role isolation

\- Effective-date correctness

\- Policy conflict handling

\- Provider failure handling

\- Invalid request handling



P1:

\- Citation integrity

\- Prompt-injection resistance

\- Unsupported business claims



P2:

\- Meaning-preserving response wording

