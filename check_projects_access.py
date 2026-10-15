"""Read-only check of the exact personal Projects discovery query."""
import os
from preflight import request

def main():
    query = '''query {
      repository(owner:"valeriykurs1992",name:"gosteo-marketplace") {
        projectsV2(first:100) { nodes { id number title shortDescription readme url public closed createdAt updatedAt }
          pageInfo { hasNextPage endCursor } }
      }
    }'''
    response = request('https://api.github.com/graphql', os.environ['PROJECTS_TOKEN'], {'query': query})
    errors = response.get('errors') or []
    if errors:
        types = sorted({str(error.get('type') or error.get('extensions', {}).get('code', 'unknown')) for error in errors})
        print('Projects discovery failed; safe GraphQL categories: ' + ', '.join(types))
        return 1
    connection = response['data']['repository']['projectsV2']
    print('Projects discovery succeeded; project count on first page: ' + str(len(connection['nodes'])))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('Projects access check failed; private details suppressed')
        raise SystemExit(1)
