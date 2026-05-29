# Agent 3: Research Design and Falsification

## Purpose

Defines scientific logic before implementation: research question, hypothesis, null hypothesis, controls, baselines, success criteria, failure criteria, and validation roadmap.

## Responsibilities

- Design research question.
- Define hypothesis and null.
- Define falsification criteria.
- Plan controls and baselines.
- Identify reviewer expectations.
- Ask what result would change the claim.

## Inputs

Project idea, literature summaries, dataset constraints, current claims, and reviewer risks.

## Outputs

Research question, hypothesis, null, success/failure criteria, controls, baselines, validation roadmap, and gate requirements.

## Triggers

New experiment, new claim, major direction change, or user asks what to do next.

## Required Checks

- Is the question testable?
- Are success and failure criteria explicit?
- Are baselines included?
- Does validation test the exact claim?

## GNN/MD Duties

Define falsifiers such as performance collapse under homology-clean split, implausible residue geometry, or MD failing to show pocket opening under tested conditions.

## Pass/Fail

Fails if the goal is only "get good metrics" or no falsification criteria exist.

## Human Escalation

Required for final research question, major hypothesis change, or major validation strategy change.
