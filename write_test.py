"""Isolated backup-account write and Git restore smoke test; no source writes."""
import base64
import os
from pathlib import Path
import subprocess
import tempfile
from preflight import request


def main():
    token = os.environ['BACKUP_TOKEN']
    name = 'backup-validation-' + os.environ['GITHUB_RUN_ID']
    env = dict(os.environ)
    env.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + base64.b64encode(('x-access-token:' + token).encode()).decode(),
        GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1')
    def git(*args, cwd=None):
        result = subprocess.run(['git', *args], cwd=cwd, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        if result.returncode:
            raise RuntimeError('Git verification failed')
        return result.stdout.decode().strip()
    request('https://api.github.com/user/repos', token,
        {'name': name, 'private': True, 'has_issues': False, 'has_wiki': False,
         'description': 'Isolated backup validation; no production data'})
    print('Private test repository created (retained, not deleted)')
    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / 'source'
        source.mkdir()
        git('init', '-b', 'main', cwd=source)
        git('config', 'user.name', 'backup-test', cwd=source)
        git('config', 'user.email', 'backup-test@users.noreply.github.com', cwd=source)
        (source / 'restore-proof.txt').write_text('backup restore proof\n')
        git('add', '.', cwd=source)
        git('commit', '-m', 'Isolated recovery fixture', cwd=source)
        sha = git('rev-parse', 'HEAD', cwd=source)
        git('branch', 'test-branch', cwd=source)
        git('tag', 'test-tag', cwd=source)
        git('branch', 'snapshots/validation/main', cwd=source)
        url = 'https://github.com/Gosteoreserv1/' + name + '.git'
        git('push', '--mirror', url, cwd=source)
        print('Commit, branch, tag and snapshot ref written')
        restored = Path(temp) / 'restored.git'
        git('clone', '--mirror', url, str(restored))
        for ref in ['refs/heads/main', 'refs/heads/test-branch', 'refs/tags/test-tag',
                    'refs/heads/snapshots/validation/main']:
            if git('rev-parse', ref, cwd=restored) != sha:
                raise RuntimeError('Restore ref mismatch')
        git('fsck', '--full', cwd=restored)
        if git('show', 'refs/heads/snapshots/validation/main:restore-proof.txt', cwd=restored) != 'backup restore proof':
            raise RuntimeError('Restored bytes mismatch')
        print('Independent clone, all test refs, snapshot bytes and git fsck verified')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Isolated write/restore test FAILED; private details suppressed')
        raise SystemExit(1)
