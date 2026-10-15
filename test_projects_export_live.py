"""Exercise actual pinned Projects exporter; other sections are stubbed, never persisted."""
import base64
import json
import os
from pathlib import Path
import tempfile
import types
import traceback
from preflight import request
from run_backup import REVISION

def main():
    source = request('https://api.github.com/repos/Gosteoreserv1/github-account-backup/contents/scripts/archive_metadata.py?ref=' + REVISION,
                     os.environ['BACKUP_TOKEN'])
    module = types.ModuleType('pinned_archive_metadata')
    exec(compile(base64.b64decode(source['content']), 'pinned_archive_metadata.py', 'exec'), module.__dict__)
    def api(token, method, path, body=None, **kwargs):
        if path == '/graphql':
            response = request('https://api.github.com/graphql', token, body)
            for error in response.get('errors') or []:
                extension = error.get('extensions', {})
                print('Safe GraphQL diagnostic: ' + str(error.get('type') or extension.get('code', 'unknown')))
                if extension.get('typeName') and extension.get('fieldName'):
                    print('Schema field: ' + str(extension['typeName']) + '.' + str(extension['fieldName']))
            return response
        return {'name': 'gosteo-marketplace', 'has_discussions': False}
    with tempfile.TemporaryDirectory() as folder:
        result = module.export_archive('gosteo-marketplace', Path(folder), 'test', 'valeriykurs1992',
            'unused-non-project-sections-are-stubbed', api, lambda *args, **kwargs: [])
        coverage = json.loads((Path(folder) / 'metadata/gosteo-marketplace/test/coverage.json').read_text())
        print('Live Projects-only component test; other API sections are stubbed; no backup status is written')
        print('Linked projects archived: ' + str(coverage['sections']['projects-v2.json'].get('count', 0)))
        print('Projects exporter errors: ' + str(len(result['errors'])))
        if result['errors']:
            kinds = set()
            for path in result['errors']:
                kinds.add('item-fields' if '/item-fields/' in path else path.rsplit('/', 1)[-1])
            print('Failed component kinds (no private IDs): ' + ', '.join(sorted(kinds)))
            return 1
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        frame = traceback.extract_tb(error.__traceback__)[-1]
        print('Live Projects component test exception: ' + type(error).__name__ +
              '; function ' + frame.name + '; line ' + str(frame.lineno))
        raise SystemExit(1)
