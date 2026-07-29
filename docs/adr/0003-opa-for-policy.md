# ADR 0003: OPA for policy

## Status

Accepted

## Context

Policy must not live only in agent prompts.

## Decision

Enforce security, change control, code standards, and PII checks via **OPA/Rego**, composed in `policy_gate` with Presidio and Guardrails.

## Consequences

- Policies are testable (`*_test.rego`)  
- Offline fallback exists for demos when OPA is down  
- AWS: run OPA on ECS/EKS; optionally complement with Verified Permissions for IAM-style authZ
