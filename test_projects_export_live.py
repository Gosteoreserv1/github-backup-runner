"""Exercise actual pinned Projects exporter; other sections are stubbed, never persisted."""
import base64
import json
import os
from pathlib import Path
import tempfile
import types
from preflight import request
from run_backup import REVISION

def main():
    source = request('https://api.github.com/repos/Gosteoreserv1/github-account-backup/contents/scripts/archive_metadata.py?ref=' + REVISION,
                     os.environ['BACKUP_TOKEN'])
    module = types.ModuleType('pinned_archive_metadata')
    exec(compile(base64.b64decode(source['content']), 'pinned_archive_metadata.py', 'exec'), module.__dict__)
    def api(token, method, path, body=None, **kwargs):
        if path == '/graphql':
            return request('https://api.github.com/graphql', token, body)
        return {'name': 'gosteo-marketplace', 'has_discussions': False}
    with tempfile.TemporaryDirectory() as folder:
        result = module.export_archive('gosteo-marketplace', Path(folder), 'test', 'valeriykurs1992',
            'unused-non-project-sections-are-stubbed', api, lambda *args, **kwargs: [])
        coverage = json.loads((Path(folder) / 'metadata/gosteo-marketplace/test/coverage.json').read_text())
        print('Live Projects-only component test; other API sections are stubbed; no backup status is written')
        print('Linked projects archived: ' + str(coverage['sections']['projects-v2.json'].get('count', 0)))
        print('Projects exporter errors: ' + str(len(result['errors'])))
        if result['errors']:
            print('Projects component test failed; private error paths suppressed')
            return 1
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('Live Projects component test failed; private details suppressed')
        raise SystemExit(1)
