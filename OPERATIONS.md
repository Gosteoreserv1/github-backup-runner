# Automatic backup operations

GitHub App push/repository events are routed through the existing Cloudflare
Worker to backup.yml. A D1 outbox retains delivery IDs and commit SHAs until a
signed runner receipt proves that the commit is reachable from a recovery snapshot.
Dispatch is not completion. Busy tasks are retained and replayed every 30 minutes.
Exact duplicate repository/commit deliveries share the verified snapshot proof.

Git history, portable branches/tags/notes and Git LFS are preserved after pushes.
GitHub may reject server-generated refs; these are not promised as portable refs.
Metadata reconciliation runs daily at 03:41 UTC (06:41 Moscow), with before/after
append-only snapshots. Issues/PR/settings are archives, not automatically restored
native GitHub objects. Export coverage documents intentional exclusions and errors.
Codespaces secret names are excluded to avoid requiring source write access.
Secret values, database/media/hosting state and registry binaries require external
backups. Uncaptured commits deleted upstream cannot be guaranteed recoverable.

Independent health checks run every 30 minutes. Telegram/email configuration is
encrypted in KV; the encryption/HMAC key remains a Worker secret and Actions secret.
Incident and recovery delivery is tracked independently for each notification channel.
Never disable validation or silence a genuine partial backup to show a green result.

Public Actions execution does not make LFS/API/Cloudflare/email storage unlimited.
No paid plan was enabled by this implementation. Account billing subscriptions were
not readable through the available Cloudflare OAuth permissions and need owner review.

Initial acceptance is still in progress: inspect the private status controller and
the active reconciliation run. Isolated event/force-delete/restore tests must pass
before claiming full end-to-end acceptance. Production Git histories are not test targets.

2026-10-10 acceptance evidence: reconciliation run 38032997797 verified Git for
19/19 source repositories (18 original plus isolated test), with metadata partial
only for gosteo-marketplace/projects-v2.json. Automatic push run 38033683046 saved
unique commit 7af121a; force-rewrite run 38034017517 saved sibling 25fe525;
branch-delete run 38034279316 succeeded. Old 7af121a and a deleted tag were restored
from backup snapshots to private backup-e2e-restored-20261010 without reading the
primary account. Personal Projects access needs a separate PROJECTS_TOKEN with
read:project scope; do not replace read-only repository credentials with broad
classic repo write access. Overall metadata acceptance remains incomplete until
the owner supplies this credential and the exporter is verified with it.
