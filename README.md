# GitHub backup runner

Public execution controller only. Private repository contents, metadata, status
ledgers and backups must never be committed here or uploaded to public artifacts.

Stage 1 checks standard GitHub Actions availability without any credentials.
This is NOT yet an active backup service. Existing private backups are unchanged.

Next stage: install least-privilege GitHub App credentials as Actions secrets;
retrieve reviewed controller scripts from a pinned private source; suppress private
data in public logs; persist status privately; integrate durable event journal,
independent watchdog, Telegram and email. Test before switching webhook routing.

Public Actions do not remove Git LFS/API/storage limits or account restrictions.
Never accept external pull-request code in a job that has backup credentials.
