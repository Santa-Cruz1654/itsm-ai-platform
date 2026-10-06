---
document_id: application-access
title: Application Access Troubleshooting
category: application
subcategory: access
version: "1"
language: en
access_level: internal
tags:
  - application
  - access
  - authorization
  - entitlement
---
# Application Access Troubleshooting

## Purpose

Use this guide when an employee cannot access an approved corporate application.

## Troubleshooting

### 1. Identify the application

Record the exact application name, environment, and URL if applicable.

Capture the complete error message.

### 2. Check account status

Confirm that the user is signed in with the correct corporate account.

If the account is locked, disabled, or affected by MFA problems, follow the account recovery procedure.

### 3. Check authorization

Application access is normally controlled through approved roles or groups.

If the user has never had access, submit the appropriate access request rather than attempting to bypass authorization.

### 4. Check whether the application is broadly affected

Ask whether other employees can access the same application.

If multiple users are affected, treat the issue as a possible service incident or outage.

### 5. Retry after normal authentication

After correcting an authentication issue, retry the application once.

Avoid repeated login attempts when the account may be subject to lockout controls.

### 6. Escalate

Escalate when:

- The user requires a new role or entitlement.
- Access was recently removed unexpectedly.
- Multiple users are affected.
- The application returns a server-side error.
- The user receives a policy or authorization denial.

## Security

Never advise users to bypass application authorization, share credentials, disable MFA, or use another employee's account.