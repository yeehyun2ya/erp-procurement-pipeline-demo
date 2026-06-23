# Project Rules For Codex

This project is an ERP procurement validation pipeline demo.

## Core Design Goal

The same quote data can follow different validation and approval paths depending on company configuration, while the validation node code stays unchanged.

## Rules

- Nodes must not know the company.
- Do not put company-specific checks such as `if company == "A"` or `if company == "B"` inside node functions.
- Company-specific branching belongs in LangGraph conditional edges.
- Company-specific rules belong in config files, later under `configs/companies/`.
- LLM output must be forced into a fixed JSON shape.
- Keep each issue inside its agreed scope.
- Explain changes in beginner-friendly language.

## Comment Style

- Keep code identifiers, file names, function names, and class names in English.
- Korean comments are allowed when they help a beginner understand tests or important code.
- For test comments, prefer Korean `준비 / 실행 / 검증` wording instead of `Given / When / Then`.
- Do not write comments that simply repeat what the code already says.
- Keep error messages and public API names in English by default.

## Current Issue Scope

Issue 2 defines the input JSON shape only.

Do not add anomaly detection, LLM calls, FastAPI, human-in-the-loop flow, TCO calculation, company config files, or company-specific conditional edges in this issue.
