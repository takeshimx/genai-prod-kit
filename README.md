# genai-prod-kit

[![eval-gate](https://github.com/takeshimx/genai-prod-kit/actions/workflows/eval-gate.yml/badge.svg)](https://github.com/takeshimx/genai-prod-kit/actions/workflows/eval-gate.yml)
[![pii-gate](https://github.com/takeshimx/genai-prod-kit/actions/workflows/pii-gate.yml/badge.svg)](https://github.com/takeshimx/genai-prod-kit/actions/workflows/pii-gate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Production harness for shipping LLM features.** Five building blocks — an
observability gateway, a prompt registry, an eval gate, PII redaction, and
drift monitoring — that take a prototype LLM call and make it safe to run in
production.

Provider-agnostic, GCP-free by default, **zero required dependencies** for the
core. `git clone`, install, and one API key is enough to run the toy example.

---

## Why this exists

Going from a working prototype (`provider.generate("...")`) to a production
LLM feature means closing a series of gates:

| Gate | Question it answers |
|------|---------------------|
| Observability | What did this call cost, how many tokens, how slow? |
| Prompt versioning | Which prompt produced this output? |
| Eval gate | Did this change make the model *worse*? |
| PII safety | Did we send personal data to a third-party API? |
| Drift | Has the live input distribution moved away from what we tested on? |

This kit packages each gate as a small, injectable component. Providers and
storage sinks are passed in, so nothing in the core is wired to a specific
vendor or cloud.

---

## How a call flows through the gates

A raw prototype call is one arrow: `your code → model → text`. Production adds a
gate before and after that arrow. Here is where each harness sits.

```
                         your feature code
                                │
                                ▼
   ┌───────────────────────────────────────────────────────────┐
   │  H2 Prompt Registry   pick {feature}/v{N}.txt, record N     │
   └───────────────────────────────────────────────────────────┘
                                │  prompt
                                ▼
   ┌───────────────────────────────────────────────────────────┐
   │  H4 PII Redaction     mask email / card before egress       │  shadow│enforce
   └───────────────────────────────────────────────────────────┘
                                │  redacted prompt
                                ▼
   ┌───────────────────────────────────────────────────────────┐
   │  H5 Drift Monitor     compare live input vs. reference      │  shadow
   └───────────────────────────────────────────────────────────┘
                                │
                                ▼
   ┌───────────────────────────────────────────────────────────┐
   │  H1 LLM Gateway   ── provider ──►  Gemini / OpenAI          │
   │                   ◄── LLMResult ──  (text, in/out tokens)    │
   │   measures tokens · cost · latency, writes 1 record ──► sink │  jsonl│bigquery
   └───────────────────────────────────────────────────────────┘
                                │  response
                                ▼
   ┌───────────────────────────────────────────────────────────┐
   │  H4 PII Restore   put originals back into the response       │
   └───────────────────────────────────────────────────────────┘
                                │
                                ▼
                          your feature code

   H3 Eval + Regression Gate runs in CI, not per-call:
   golden set → accuracy → block the merge if it regressed > threshold.
```

Each box is independent and injectable — drop one in or leave it out without
touching the others. The provider (Gemini/OpenAI) and the sink (jsonl/bigquery)
are the only vendor-specific pieces, and both are passed in.

---

## The five harnesses

| # | Harness | Module | What it gives you |
|---|---------|--------|-------------------|
| H1 | **LLM Gateway** | `gateway.py` | Single entry point. Records tokens / cost / latency per call to a pluggable sink. fail-loud on provider errors, log-quietly on sink errors. |
| H2 | **Prompt Registry** | `prompts/registry.py` | `{feature}/v{N}.txt` versioning; the active version is recorded on every call. |
| H3 | **Eval + Regression Gate** | `evals/` | Golden set, accuracy/latency, blocks a merge when accuracy regresses. |
| H4 | **PII Redaction** | `pii/` | Reversible masking with shadow / enforce modes. |
| H5 | **Drift Monitoring** | `drift/` | KS / PSI / Chi-square over a reference vs. detection window; shadow by default. |

---

## Install

```bash
# core only — no third-party dependencies
pip install -e .

# add a provider when you want to make real calls
pip install -e ".[gemini]"    # Gemini
pip install -e ".[openai]"    # OpenAI

# optional extras
pip install -e ".[ner]"       # Tier-2 NER for PII
pip install -e ".[bigquery]"  # BigQuery sink
pip install -e ".[dev]"       # pytest
```

> The quotes around `".[gemini]"` matter in zsh, which otherwise tries to
> expand the brackets as a glob.

---

## Quickstart (one real call)

```bash
export GEMINI_API_KEY=...      # your key, never commit it
python examples/toy_feature/run.py
```

`run.py` wires the pieces together — registry → gateway → sink:

```python
from genai_prod_kit.gateway import call_llm
from genai_prod_kit.providers.gemini import GeminiProvider
from genai_prod_kit.sinks.jsonl import JsonlSink
from genai_prod_kit.prompts.registry import get_prompt

provider = GeminiProvider(api_key)
sink = JsonlSink("invocations.jsonl")
version, template = get_prompt("toy_summary")

result = call_llm(
    template.format(text="..."),
    provider=provider,
    sink=sink,
    feature="toy_summary",
    model="gemini-2.5-flash",
    prompt_version=version,
)
print(result.text)
# one record (tokens / cost / latency / prompt_version) is appended to invocations.jsonl
```

Run the eval gate against the golden set (also a real call):

```bash
python examples/toy_feature/run_eval.py
# accuracy = 100.0%  (N items) -> appended to eval_runs.jsonl
```

---

## Design principles

- **provider-agnostic** — `LLMProvider` is a `Protocol`; swap Gemini / OpenAI
  behind one interface without touching the gateway.
- **storage-agnostic** — the default `JsonlSink` writes local JSON Lines.
  BigQuery and others are optional adapters behind the `InvocationSink`
  protocol.
- **domain-decoupled** — eval targets, PII dictionaries, and drift
  `FeatureSpec`s are injected as configuration. No domain values are
  hardcoded in the core.

---

## From prototype to production: what each gate prevents

A prototype call works on the happy path. Each harness exists because of a
specific way that same call fails once real traffic, real money, and real users
hit it.

| Harness | The production failure it prevents | What you can answer after |
|---------|-----------------------------------|---------------------------|
| **H1 Gateway** | "This feature's bill tripled and no one noticed." Cost, tokens, and latency are invisible when each call site talks to the SDK directly. | *What does this feature cost per month? Which call is slow?* — one record per call, in one place. |
| **H2 Prompt Registry** | "Accuracy dropped last Tuesday and we can't tell which prompt edit did it." Prompts live in code, untracked. | *Which prompt version produced this output?* — the version is recorded on every call. |
| **H3 Eval Gate** | "A 'small' prompt tweak quietly regressed accuracy and shipped." Unit tests check shape, not quality. | *Did this change make the model worse?* — the merge is blocked when accuracy drops past a threshold. |
| **H4 PII Redaction** | "We sent a customer's email and card number to a third-party API." Raw user text goes straight to the vendor. | *Did any personal data leave our boundary?* — structured PII is masked before egress, restored after. `shadow` observes first, `enforce` acts. |
| **H5 Drift Monitor** | "The model degraded for weeks because real inputs drifted from what we evaluated on." Offline accuracy stays green while production rots. | *Has the live input distribution moved?* — a leading signal (KS/PSI/Chi-square) fires before accuracy visibly falls. |

The throughline: **none of these is the model's job — they are the operator's
job.** This kit is the operator's half, kept separate from any one vendor so the
model underneath can change without the safety net changing.

---

## Project layout

```
genai-prod-kit/
├── src/genai_prod_kit/
│   ├── gateway.py            # H1: single entry point + InvocationRecord
│   ├── pricing.py            # per-model unit prices (single source of truth)
│   ├── providers/            # gemini + openai (both implemented)
│   ├── sinks/                # jsonl (bigquery optional)
│   ├── prompts/registry.py   # H2: {feature}/v{N}.txt
│   ├── evals/                # H3: runner + regression gate + golden sets
│   ├── pii/                  # H4: detector / redactor / restorer / pipeline
│   └── drift/                # H5: statistics (KS/PSI/Chi2) + monitor + config
├── examples/toy_feature/     # minimal, domain-free runnable example
├── notebooks/                # cookbook (see plan)
└── tests/
```

---

## Status

H1–H5 are implemented and verified. Gemini and OpenAI providers both run the
same gateway code. The test suite (17 offline tests, zero API cost) and CI
(eval-gate, pii-gate) are in place. The cookbook notebooks (01–07) are written;
02–06 are pending a local run.

## License

[MIT](LICENSE).
