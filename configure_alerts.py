"""Transfer only notification configuration to the authenticated fixed Worker."""
import hashlib
import hmac
import json
import os
import time
import urllib.request

def main():
    fields = ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'RESEND_API_KEY',
              'BACKUP_ALERT_FROM', 'BACKUP_ALERT_EMAIL')
    payload = {field: os.environ[field] for field in fields}
    payload['timestamp'] = int(time.time() * 1000)
    body = json.dumps(payload).encode()
    signature = 'sha256=' + hmac.new(os.environ['BACKUP_CALLBACK_SECRET'].strip().encode(), body, hashlib.sha256).hexdigest()
    request = urllib.request.Request('https://github-backup-webhook.kurs19992.workers.dev/backup/configure-alerts',
        body, {'Content-Type': 'application/json', 'User-Agent': 'GOSTEO-backup-runner/1.0',
               'x-backup-signature': signature}, method='POST')
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError()
    print('Independent notification configuration accepted; no credentials logged')

if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        print('Notification configuration rejected; HTTP status ' + str(error.code))
        raise SystemExit(1)
    except Exception:
        print('Notification configuration failed; private details suppressed')
        raise SystemExit(1)
