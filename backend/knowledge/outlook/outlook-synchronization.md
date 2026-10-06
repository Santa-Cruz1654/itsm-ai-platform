---
document_id: outlook-synchronization
title: Outlook Synchronization Troubleshooting
category: email
subcategory: outlook
version: "1"
language: en
access_level: internal
tags:
  - outlook
  - email
  - synchronization
  - office-365
---
# Outlook Synchronization Troubleshooting

## Purpose

Use this guide when Outlook is not synchronizing new mail, sent items, calendar changes, or folders with the corporate mailbox.

## Symptoms

Common symptoms include:

- New messages are delayed or missing.
- Outlook shows "Disconnected", "Trying to connect", or repeated synchronization errors.
- Mail appears in webmail but not in the Outlook desktop client.
- Sent messages remain in the Outbox.
- Calendar or folder changes do not appear across devices.

## Troubleshooting

### 1. Check connectivity

Confirm that the device has working corporate network or Internet access.

If the user is working remotely, confirm that the approved corporate VPN is connected when the organization requires VPN access for mailbox connectivity.

### 2. Check Outlook connection status

In Outlook, inspect the connection status shown by the client.

If Outlook reports that it is disconnected, reconnect the device to the required network and allow Outlook a short period to synchronize.

### 3. Compare with webmail

Open the organization's approved webmail service.

- If the message is present in webmail but missing in Outlook, the mailbox is reachable and the issue is likely limited to the Outlook client.
- If the message is missing in both places, the issue may be server-side or account-related and should be escalated.

### 4. Restart Outlook

Close Outlook completely and reopen it.

Allow synchronization to complete before repeatedly restarting the client.

### 5. Check the Outbox

If messages are stuck in the Outbox:

1. Confirm connectivity.
2. Check whether the message contains unusually large attachments.
3. Allow Outlook to reconnect.
4. Retry the send operation.

### 6. Check account authentication

If Outlook repeatedly asks for credentials, verify that the user is signing in with the approved corporate account.

If the account is locked or MFA is failing, use the MFA / Account Lockout procedure or contact the service desk.

### 7. Escalate

Escalate when:

- Webmail and Outlook both fail.
- Multiple users are affected.
- Synchronization remains broken after connectivity and client restart checks.
- The mailbox or account appears disabled.
- The issue requires administrative mailbox changes.

## Important

Do not delete the Outlook profile or mailbox data as a first troubleshooting step. Profile recreation should be performed only through the approved service-desk procedure.