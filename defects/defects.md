# Defect Reports

## DEF-001 - Incorrect policy used for Atlas contractor

### Recording
02

### Expected
Atlas contractor on 2026-09-21 should use P05.

Expected limit:

INR 10,000

### Actual
Response uses P02 and returns INR 25,000.

### Evidence
Observed citation:

P02

P02 applies to Atlas employees, not contractors.

### Impact
A contractor can receive an incorrect reimbursement limit.

### Severity
Critical

### Next Diagnostic Step
Inspect authorization/eligibility filtering before retrieval and generation.

---

## DEF-002 - Effective-date boundary uses expired policy

### Recording
03

### Expected
On 2026-06-01, P02 is effective.

### Actual
P01 is returned.

### Impact
Users can receive a policy that expired on the requested date.

### Severity
Critical

### Next Diagnostic Step
Test policy date comparison at both effective_from and effective_to boundaries.

---

## DEF-003 - Contradictory policies silently resolved

### Recording
04

### Expected
CONFLICT because P07 and P08 are simultaneously applicable and no precedence rule exists.

### Actual
ANSWERED with INR 12,000 using P07.

### Impact
The user receives one policy value without evidence that it should take precedence.

### Severity
Critical

### Next Diagnostic Step
Inspect conflict detection after eligibility filtering and before generation.

---

## DEF-004 - Citation quote does not match cited policy

### Recording
06

### Expected
Citation P02 must quote the actual P02 passage.

### Actual
Citation claims P02 says INR 35,000.

Actual P02 says INR 25,000.

### Impact
The citation cannot support the factual response and weakens auditability.

### Severity
High

### Next Diagnostic Step
Verify citation generation and response validation.

---

## DEF-005 - Provider timeout mapped to business outcome

### Recording
07

### Expected
HTTP 503 for provider timeout.

### Actual
HTTP 200 with INSUFFICIENT_EVIDENCE.

### Impact
An infrastructure/provider failure is presented as a policy evidence result.

### Severity
Critical

### Next Diagnostic Step
Verify provider exception-to-HTTP mapping and ensure provider failures cannot become business-outcome statuses.


---

## Don't commit yet

**For now, only create these folders/files and populate the files above.**

Then run:

```powershell
python -m pytest -q