# ADR 0002: Declarative DAG

## Status

Accepted

## Context

Hardcoding stage order in workflow code makes governance and scenario branching opaque.

## Decision

Define the pipeline in [`dag/sdlc.yaml`](../../dag/sdlc.yaml); workflows interpret it at runtime.

## Consequences

- Stage graph is reviewable as data  
- Master workflow stays generic  
- Schema validation catches DAG authoring errors early
