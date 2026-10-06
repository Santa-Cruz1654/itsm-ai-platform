---
document_id: mfa-account-lockout
title: MFA and Account Lockout Troubleshooting
category: identity
subcategory: mfa
version: "1"
language: en
access_level: internal
tags:
  - mfa
  - identity
  - account-lockout
  - authentication
---
# MFA and Account Lockout Troubleshooting

## Purpose

Use this guide when an employee cannot complete multi-factor authentication or believes the corporate account is locked.

## MFA Troubleshooting

### 1. Confirm the account

Verify that the user is attempting to authenticate with the correct corporate account.

### 2. Check the MFA method

Confirm that the approved MFA method is available and that the user can receive or approve the authentication challenge.

### 3. Check device time

If the approved authenticator application uses time-based codes, verify that the device date and time are synchronized automatically.

Do not manually alter time settings to bypass authentication controls.

### 4. Retry carefully

Avoid repeated failed authentication attempts.

Repeated failures may trigger account protection or lockout controls.

## Account Lockout

If the account is locked:

1. Stop repeated login attempts.
2. Confirm the user identity through the organization's approved support process.
3. Use the approved account-unlock or recovery workflow.
4. If the user cannot complete identity verification or recovery, escalate to the service desk or identity team.

## Security

Never disable MFA, request MFA codes from another person, share recovery codes, or use another employee's account.

Support personnel must follow the organization's identity-verification requirements before performing account recovery or unlock operations.

## Escalation

Escalate when:

- The user cannot complete approved identity verification.
- MFA enrollment is corrupted or unavailable.
- The account is repeatedly locked without an obvious cause.
- Multiple employees experience MFA failures.
- An identity-provider outage is suspected.