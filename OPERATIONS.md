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

2026-10-15 maintenance: the actual Projects exporter passed live component run
38788776535 using the separate read:project token. It archives all primary-owned
boards in each metadata archive, including boards whose private repository links
GitHub redacts. coverage.json records redacted link/content counts; this does NOT
promise fully restorable Projects views, automations or private item linkage.
An independent read-only audit found matching heads/tags/notes for 21/21 source
repositories, and all 153 unique journal commit SHAs reachable in snapshots.
This audit does not check LFS payload bytes or commits never captured in the journal.
Telegram/email test run 38698272627 was accepted by both providers; provider
acceptance is not proof that a message was read. Incident reminders repeat daily
while unhealthy, with independent recovery delivery for each channel. A successful
full manual reconciliation can supersede an older failed scheduled run; a green
single-repository push cannot. Generated status documents are kept atomic during
publication, and mutable metadata/status are loaded from current private main,
independently of the immutable controller code pin. Full acceptance still requires
the latest Backup ALL run and private coverage report to pass.

Full reconciliation 38788853428 completed successfully on 2026-10-15 at 19:08 UTC:
21/21 repositories, zero failed; marketplace coverage has zero export errors and
34 saved binary object records. An independent watchdog subsequently identified
two older repository-creation deliveries still awaiting receipt; these were
replayed rather than manually marked complete. This is separate from Git ref
coverage, which already matched. Check-only workflow must fail when health is
false; HTTP 200 alone is not a healthy result.

Final maintenance validation: full run 38789090430 also passed 21/21 with zero
failures. Replays 38792663521 and 38794206970 completed both older creation
deliveries. Independent check 38794446946 returned healthy=true on 2026-10-15
19:30 UTC, automatically closed watchdog issue #12, and recorded successful
recovery delivery states for both Telegram and email. Historical issue #13 was
closed only after this evidence. Fresh deliveries may still be queued normally;
busy retries are replayed by the 30-minute scheduler, not marked complete early.

Fresh dev push proof: run 38794835605 succeeded; primary and backup dev both
resolve to 79c69f53f0dfd1ac439348c96e2427e181d943e6. Its signed snapshot receipt
completed the remaining journal entry: 164 complete, zero pending/dispatched.
The event ledger retained successful metadata timestamp 2026-10-15T190852Z
while advancing Git backup timestamp to 2026-10-15T193333Z. Latest single-repo
status is success=1, failed=0, total=1; full coverage evidence remains the
separate successful 21-repository reconciliations above.
