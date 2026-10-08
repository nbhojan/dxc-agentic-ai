# ADR-001 — ClaimsCopilot: model and deployment decision

| | |
|---|---|
| **Version** | v1 *(change to v2 in the second file)* |
| **Status** | Proposed |
| **Author** | *Bindu Priya P* · Team *2* |
| **Date** | *08/10/2026* |


---

## 1. Context
ClaimsCopilot will help 3,200 claims staff summarize claim files, answer policy questions, and draft English/Hindi customer letters. Claim files contain personal and health data, so the initial design keeps inference in AWS's Mumbai region, subject to Compliance approval.
The pilot must be ready in 8 weeks, the team has no dedicated MLOps/GPU engineer, and the running-cost budget is USD 4,000 per month. Summaries must meet a <2% factual-error target and a human adjuster approves customer-facing content.

## 2. Decision drivers
Ranked from most important to least important:

1. Protect personal and health data and keep processing in India.
2. Meet the 8-week pilot deadline with a small team and little GPU-operations experience.
3. Meet the summary quality target and keep a human in the approval loop.
4. Keep estimated model usage within the USD 4,000 monthly budget while handling traffic spikes.

## 3. Options considered

| Option (path + pay model + model) | Pros | Cons |
|---|---|---|
| **A. AWS public-cloud managed model API in Mumbai + pay-as-you-go + small/mid-tier proprietary models (recommended)** | Fast to pilot; scales for peaks; little GPU operations; AWS agreement already exists. | Per-token bill can grow; exact model and regional availability must be checked; provider dependency. |
| **B. VMware in Chennai + self-hosted open-weight models on the existing GPUs + provisioned capacity** | Strong infrastructure control; avoids per-token API charges; uses already-purchased hardware. | Team lacks GPU/MLOps skills; deployment, security, scaling and model evaluation add risk to the 8-week deadline; spare hardware does not make operations free. |
| **C. AWS public-cloud managed API in Mumbai + pay-as-you-go + mid-tier proprietary model for every workload** | One model tier simplifies evaluation and operations; likely stronger quality than the small tier. | At the helper calculator's illustrative rates, estimated model usage is about USD 5,010/month, above budget; also pays mid-tier rates for simpler Q&A. |

## 4. Decision
**We will use** AWS's managed model API **with** pay-as-you-go billing **and** mid-tier models for summaries and letters plus a small model for policy Q&A **in** the Mumbai region (`ap-south-1`) **because** this is the fastest path for our small team and keeps processing in India, subject to Compliance approval and model-region verification.

| Workload | Model | Why |
|---|---|---|
| 1 · Claim summary | Mid-tier proprietary model API; illustrative calculator rate: $3/1M input tokens and $15/1M output tokens. | Long, complex claim documents and the <2% factual-error target justify starting with the stronger tier. Benchmark against reviewed examples; an adjuster checks every summary. |
| 2 · Policy Q&A | Small proprietary model API; illustrative calculator rate: $0.10/1M input tokens and $0.40/1M output tokens. | Ground answers in retrieved policy passages, cite those passages, and abstain when evidence is weak. This is an internal adjuster workflow, so the lower-cost tier is a testable starting point. |
| 3 · Customer letters | Mid-tier proprietary model API; illustrative calculator rate: $3/1M input tokens and $15/1M output tokens. | Start with the stronger tier for English and Hindi drafting; evaluate both languages and require adjuster approval before sending. |

## 5. Data residency & protection
Process requests only in AWS Mumbai (`ap-south-1`) using private connectivity (such as a VPC endpoint) where supported. Before launch, verify that each selected model is available in that region and that requests do not use cross-region inference; if not, choose another in-region model or pause that workload until Compliance approves an alternative.
Encrypt data in transit and at rest, apply least-privilege access, and do not use customer prompts to train models. Restrict prompt access to authorized claims staff and service operators. Log request IDs, model/version, latency, token counts and safety outcomes for audit and cost control, but do not put full prompts, health documents or generated letters in application logs. Confirm retention and deletion settings with Compliance before the pilot.

## 6. Cost estimate (per month)

| Workload | Calculation | USD / month |
|---|---|---|
| 1 · Summary | 40,000 claims × ((25,000 input × $3) + (800 output × $15)) / 1,000,000 | $3,480 |
| 2 · Q&A | 2,500 questions/day × 30 days × ((4,000 input × $0.10) + (400 output × $0.40)) / 1,000,000 | $42 |
| 3 · Letters | 15,000 letters × ((1,500 input × $3) + (500 output × $15)) / 1,000,000 | $180 |
| **Total** | **$3,480 + $42 + $180** | **$3,702** |

*Fits the USD 4,000 budget?* Yes, on these illustrative model-token rates, with only about **$298 (7.5%)** remaining. The calculator rates are not a live AWS quote and this estimate excludes embeddings, retrieval/storage, networking, taxes, retries, fallback-model use and other service costs. Confirm actual in-region prices before launch; track usage daily, set per-workload quotas and alerts, and reduce input/output tokens or reconsider the model mix if the full bill approaches the cap. The estimate uses average monthly volume, so test the 3× morning peak separately.

## 7. Consequences
- **Easier:** A managed API avoids running GPU infrastructure, supports a quick pilot, and can scale more easily for weekday and seasonal peaks. Workload-specific tiers avoid paying mid-tier rates for every request.
- **Harder:** Per-token spending needs active controls; regional model availability and Hindi quality must be verified; proprietary APIs create provider dependency.
- **Risks and how we reduce them:** The cost estimate has little headroom, so measure real token use, set quotas/alerts and load-test peak traffic. Models can omit or invent facts, so benchmark summaries against human-reviewed cases, require citations for policy answers, allow abstention, and keep adjuster approval before customer communication. Compliance has not formally signed off, so obtain approval for region, retention and access controls before using real customer data.
- **How we change our mind later (exit plan):** Put model calls behind a provider-neutral application interface and retain a versioned evaluation set. After 1–2 months, compare real traffic, quality and full costs; benchmark an open-weight model on the existing Chennai GPUs for a steady workload only if an operations owner and security controls are in place. Move workloads only after quality, residency and total-cost tests pass.

## 8. Rejected options — in one line each
- Self-host every workload on the VMware GPUs now: rejected because the team has no dedicated GPU/MLOps engineer and the 8-week pilot leaves little time to build and operate a secure model platform.
- Use a mid-tier model for every request: rejected because the illustrative estimate is about USD 5,010/month, above budget, and simple grounded Q&A does not justify that tier by default.
