"""Execute a pinned private controller without exposing private logs publicly."""
import base64
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request
import json
import hmac
import hashlib

CONTROLLER = 'https://github.com/Gosteoreserv1/github-account-backup.git'
REVISION = '08e6a7566796bdf1c436b304b8d53c597f7c44f9'


def configuration(env):
    for name in ('PRIMARY_TOKEN', 'BACKUP_TOKEN', 'PRIMARY_METADATA_TOKEN'):
        if not env.get(name):
            raise ValueError('Required access secrets are missing')
    target = env.get('TARGET_REPOSITORY', '')
    if target and not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', target):
        raise ValueError('Invalid repository name')
    delivery = env.get('DELIVERY_ID', '')
    if delivery and not re.fullmatch(r'[A-Za-z0-9-]{1,100}', delivery):
        raise ValueError('Invalid delivery ID')
    sha = env.get('EXPECTED_SHA', '')
    if sha and not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Invalid expected SHA')
    result = dict(env)
    auth = base64.b64encode(('x-access-token:' + env['BACKUP_TOKEN']).encode()).decode()
    result.update(GIT_CONFIG_COUNT='1',
                  GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
                  GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + auth,
                  GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1',
                  PRIMARY_OWNER='valeriykurs1992', BACKUP_OWNER='Gosteoreserv1',
                  CREATE_SNAPSHOT='true', MAX_ATTEMPTS='3')
    # Pushes preserve Git immediately; expensive API metadata reconciliation is
    # daily (or explicit manual), avoiding hundreds of API calls on every push.
    result['EXPORT_METADATA'] = 'false' if delivery and sha else 'true'
    return result


def execute(env, command=subprocess.run):
    configured = configuration(env)
    with tempfile.TemporaryDirectory(prefix='private-backup-') as temp:
        root = Path(temp)
        checkout = root / 'controller'
        # No public artifact or exception dump may contain private script output.
        with (root / 'private.log').open('wb') as log:
            def run(args, cwd=None, check=True):
                result = command(args, cwd=cwd, env=configured, stdout=log,
                                 stderr=subprocess.STDOUT, timeout=6600)
                if check and result.returncode:
                    raise RuntimeError('Private backup operation failed')
                return result.returncode
            run(['git', 'clone', '--no-checkout', CONTROLLER, str(checkout)])
            run(['git', 'checkout', '--detach', REVISION], checkout)
            result = run(['python3', 'scripts/backup.py'], checkout, check=False)
            run(['git', 'config', 'user.name', 'github-backup-bot'], checkout)
            run(['git', 'config', 'user.email', 'github-backup-bot@users.noreply.github.com'], checkout)
            run(['git', 'add', 'metadata', 'status'], checkout)
            changed = run(['git', 'diff', '--cached', '--quiet'], checkout, check=False)
            if changed == 1:
                run(['git', 'commit', '-m', 'backup: public runner result'], checkout)
                run(['python3', 'scripts/push_controller.py'], checkout)
            elif changed != 0:
                raise RuntimeError('Private status verification failed')
            if result == 0 and env.get('DELIVERY_ID'):
                expected = env.get('EXPECTED_SHA', '')
                if expected:
                    verify_archived_commit(configured, expected, root, log, command)
                receipt(env)
            return result


def verify_archived_commit(env, sha, root, log, command=subprocess.run):
    """An event SHA must be reachable from a persistent snapshot ref."""
    repository = env['TARGET_REPOSITORY']
    snapshot = root / 'snapshot-proof.git'
    result = command(['git', 'clone', '--mirror', '--filter=blob:none',
        f'https://github.com/Gosteoreserv1/{repository}--snapshots.git', str(snapshot)],
        env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    if result.returncode:
        raise RuntimeError('Snapshot proof unavailable')
    result = command(['git', '-C', str(snapshot), 'for-each-ref', '--contains=' + sha,
        '--format=%(refname)', 'refs/heads/snapshots/', 'refs/tags/snapshots/'],
        env=env, stdout=subprocess.PIPE, stderr=log, timeout=300)
    if result.returncode or not result.stdout.strip():
        raise RuntimeError('Event commit is not protected by a snapshot')


def receipt(env):
    # Never mark a journal event complete before backup + private status push.
    secret = env.get('BACKUP_CALLBACK_SECRET', '').strip()
    if not secret or not env.get('TARGET_REPOSITORY') or not env.get('GITHUB_RUN_ID'):
        raise RuntimeError('Journal callback credentials missing')
    body = json.dumps({'delivery': env['DELIVERY_ID'],
                      'repository': env['TARGET_REPOSITORY'],
                      'sourceSha': env.get('EXPECTED_SHA', ''),
                      'runId': env['GITHUB_RUN_ID'], 'verified': True}).encode()
    signature = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    request = urllib.request.Request(
        'https://github-backup-webhook.kurs19992.workers.dev/backup/receipt', body,
        {'Content-Type': 'application/json', 'User-Agent': 'GOSTEO-backup-runner/1.0',
         'x-backup-signature': signature}, method='POST')
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError('Journal callback rejected')


def alert(env):
    """Both channels are independent; no raw HTTP exceptions or URLs are logged."""
    message = 'GOSTEO backup failed or is incomplete. Check the private controller status.'
    failures = 0
    destinations = []
    if env.get('TELEGRAM_BOT_TOKEN') and env.get('TELEGRAM_CHAT_ID'):
        destinations.append(('https://api.telegram.org/bot' + env['TELEGRAM_BOT_TOKEN'] + '/sendMessage',
            {'chat_id': env['TELEGRAM_CHAT_ID'], 'text': message}, None, 'ok'))
    if all(env.get(k) for k in ('RESEND_API_KEY', 'BACKUP_ALERT_FROM', 'BACKUP_ALERT_EMAIL')):
        destinations.append(('https://api.resend.com/emails', {'from': env['BACKUP_ALERT_FROM'],
            'to': [env['BACKUP_ALERT_EMAIL']], 'subject': 'GOSTEO backup alert', 'text': message},
            env['RESEND_API_KEY'], 'id'))
    for url, payload, token, success_field in destinations:
        try:
            headers = {'Content-Type': 'application/json'}
            if token:
                headers['Authorization'] = 'Bearer ' + token
            request = urllib.request.Request(url, json.dumps(payload).encode(), headers, method='POST')
            with urllib.request.urlopen(request, timeout=20) as response:
                if not json.load(response).get(success_field):
                    failures += 1
        except Exception:
            failures += 1
    print(f'Notification channels configured: {len(destinations)}; failed: {failures}')


if __name__ == '__main__':
    try:
        code = execute(os.environ)
    except Exception:
        code = 1
    if code:
        print('Backup failed or incomplete. Private logs are intentionally not published.')
        alert(os.environ)
    else:
        print('Private backup and status persistence completed successfully.')
    raise SystemExit(code)
