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

## Stage 2 (prepared, disabled)

`backup.yml` supports manual repository synchronization and daily full-account
reconciliation. It does nothing until repository variable BACKUP_RUNNER_ENABLED
is exactly `true`. Keep this disabled until credentials and integration tests pass.
The old event webhook routing has NOT been switched to this runner.

Secrets required: PRIMARY_TOKEN, PRIMARY_METADATA_TOKEN, BACKUP_TOKEN.
Optional notification secrets: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
RESEND_API_KEY, BACKUP_ALERT_FROM, BACKUP_ALERT_EMAIL. Missing channels are
explicitly reported on failure. Credentials must be entered through GitHub Secrets.

The wrapper clones the private controller and checks out a reviewed immutable SHA.
Private output is redirected to temporary files, never public logs/artifacts, and
deleted with the temporary directory. Private status/metadata are committed only
to the private controller. Public notifications contain no repository contents.
Repository names and manual input values may still be visible in run metadata.

`python3 -m unittest -v test_run_backup.py` uses fake subprocesses and no credentials.
These tests are not an end-to-end backup or restore test. No GitHub App credential
migration, persistent event journal, duplicate suppression, recovery notification,
or independent heartbeat watchdog has been activated yet. Notifications from this
wrapper cannot report a job which never starts; the independent watchdog is needed.
Git backup retries are supplied by the pinned controller, not by copying all data
again in an outer retry loop. Allow GitHub metadata coverage gaps to remain explicit.

## Durable event verification (not deployed yet)

The worker integration passes delivery_id and source_sha. The runner checks that
the source SHA is reachable from a snapshot branch/tag before sending its signed
receipt. Missing event commits keep the task unresolved even when newer history
was copied successfully. Deletion events verify the deleted branch's previous SHA.
Repository metadata-only events do not have a commit SHA.

BACKUP_CALLBACK_SECRET must be a separate matching secret in runner and worker.
Worker D1 schema and JOURNAL binding must be installed before enabling this path.
Do not route events to the public runner while it is disabled or unconfigured.
Cloudflare scheduled replay and GitHub daily reconciliation are complementary.
This still cannot recover an uncaptured SHA after it disappears from GitHub;
source branch protections and early capture are required to limit that risk.
