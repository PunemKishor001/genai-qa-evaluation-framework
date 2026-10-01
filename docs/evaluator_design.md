\# Evaluator Design



The evaluator is deterministic and operates entirely on the supplied synthetic

policy corpus and recorded observations.



\## Evaluation flow



Request

&#x20; -> Caller validation

&#x20; -> Policy eligibility

&#x20; -> Generation-context validation

&#x20; -> Question/policy relevance

&#x20; -> Conflict detection

&#x20; -> Business status

&#x20; -> Citation integrity

&#x20; -> Unsupported-claim checks

&#x20; -> Factual-value checks

&#x20; -> Record-level verdict



\## Key principles



1\. Eligibility is based on caller tenant, role, approval state and effective date.

2\. Multiple eligible policies are not automatically a conflict.

3\. A conflict requires multiple relevant policies addressing the same subject with contradictory values.

4\. Citation IDs must reference known policy chunks.

5\. Citation quotations must match the referenced policy passage.

6\. Meaning-preserving wording must not fail solely because exact sentence wording differs.

7\. Invalid requests must not invoke generation.

8\. Provider failures must be represented explicitly.



The evaluator does not use an external LLM, API key, cloud account or external dataset.

