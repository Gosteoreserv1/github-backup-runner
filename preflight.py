"""Read-only access checks and explicitly requested test notifications."""
import json
import os
import urllib.request


def request(url, token=None, payload=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'backup-preflight'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, headers=headers,
        data=json.dumps(payload).encode() if payload is not None else None)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main():
    failures = []
    for secret, owner in [('PRIMARY_TOKEN', 'valeriykurs1992'),
                          ('PRIMARY_METADATA_TOKEN', 'valeriykurs1992'),
                          ('BACKUP_TOKEN', 'Gosteoreserv1')]:
        try:
            token = os.environ[secret]
            if request('https://api.github.com/user', token)['login'].lower() != owner.lower():
                raise ValueError()
            request('https://api.github.com/user/repos?affiliation=owner&per_page=1', token)
            if secret == 'BACKUP_TOKEN':
                request('https://api.github.com/repos/Gosteoreserv1/github-account-backup/contents/scripts/backup.py', token)
            print(secret + ': read access OK; write/metadata coverage not yet proven')
        except Exception:
            failures.append(secret)
            print(secret + ': check FAILED (details suppressed)')
    message = 'GOSTEO: test notification only. Backup is not activated yet.'
    try:
        result = request('https://api.telegram.org/bot' + os.environ['TELEGRAM_BOT_TOKEN'] + '/sendMessage',
                         payload={'chat_id': os.environ['TELEGRAM_CHAT_ID'], 'text': message})
        if not result.get('ok'):
            raise ValueError()
        print('Telegram: test accepted')
    except Exception:
        failures.append('Telegram')
        print('Telegram: test FAILED (details suppressed)')
    try:
        result = request('https://api.resend.com/emails', os.environ['RESEND_API_KEY'],
                         {'from': os.environ['BACKUP_ALERT_FROM'],
                          'to': [os.environ['BACKUP_ALERT_EMAIL']],
                          'subject': 'GOSTEO backup test', 'text': message})
        if not result.get('id'):
            raise ValueError()
        print('Email: test accepted; inbox delivery requires confirmation')
    except Exception:
        failures.append('Email')
        print('Email: test FAILED (details suppressed)')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
