---
name: security-review
description: Review caching safety, tenant isolation, and secret redaction.
---

# Skill: Security Review

## Purpose
Ensure cache isolation, redaction, tenant safety, secret scanning, authorization boundaries, and side-effecting agent workflows are safely implemented.

## Pre-Checks
1. Check that logs are correctly configured with `structlog` redaction filters.
2. Verify that tenant metadata fields are populated correctly in the gateway.

## Stepwise Workflow
1. Verify exact caching keys include `tenant_scope` and `auth_scope`.
2. Ensure side-effecting tools bypass semantic caches.
3. Validate that PII or sensitive keys are stripped out of logs and metrics labels.
4. Scan `.env` and docker-compose files to make sure no secrets are hardcoded.

## Stop Conditions (Requires Human Approval)
- Any destructive database/cache clearing operations.
- Modifying IAM or RBAC structures in external tools.
