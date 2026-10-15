"""Read-only check of the exact personal Projects discovery query."""
import os
from preflight import request

def main():
    identity = request('https://api.github.com/user', os.environ['PROJECTS_TOKEN'])
    print('Projects credential belongs to primary account: ' + str(identity.get('login', '').lower() == 'valeriykurs1992'))
    owner_query = '''query { user(login:"valeriykurs1992") { projectsV2(first:100) {
      nodes { id number title shortDescription readme url public closed createdAt updatedAt }
      pageInfo { hasNextPage endCursor } } } }'''
    owner_response = request('https://api.github.com/graphql', os.environ['PROJECTS_TOKEN'], {'query': owner_query})
    owner_errors = owner_response.get('errors') or []
    print('Owner-level Projects catalog readable: ' + str(not owner_errors))
    if not owner_errors:
        projects = owner_response['data']['user']['projectsV2']['nodes']
        print('Owner-level catalog count: ' + str(len(projects)))
        if projects:
            fields_query = '''query($id:ID!) { node(id:$id) { ... on ProjectV2 {
              fields(first:100) { nodes { ... on ProjectV2FieldCommon { id name dataType } } }
              items(first:100) { nodes { id type content { ... on Issue { id number title body url }
                ... on PullRequest { id number title body url } ... on DraftIssue { id title body } } } }
              repositories(first:100) { nodes { id nameWithOwner } }
            } } }'''
            fields = request('https://api.github.com/graphql', os.environ['PROJECTS_TOKEN'],
                             {'query': fields_query, 'variables': {'id': projects[0]['id']}})
            print('Project details query readable: ' + str(not fields.get('errors')))
            if fields.get('errors'):
                print('Project details error categories: ' + ', '.join(sorted({str(e.get('type', 'unknown')) for e in fields['errors']})))
            else:
                data = fields['data']['node']
                print('Project item types: ' + ', '.join(sorted({item['type'] for item in data['items']['nodes']})))
                print('Linked repository count visible: ' + str(len(data['repositories']['nodes'])))
    minimal = '''query { repository(owner:"valeriykurs1992",name:"gosteo-marketplace") {
      projectsV2(first:100) { nodes { id } pageInfo { hasNextPage endCursor } } } }'''
    minimal_response = request('https://api.github.com/graphql', os.environ['PRIMARY_METADATA_TOKEN'], {'query': minimal})
    print('Repository-linked IDs readable with metadata credential: ' + str(not minimal_response.get('errors')))
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
        return 0 if not owner_errors else 1
    connection = response['data']['repository']['projectsV2']
    print('Projects discovery succeeded; project count on first page: ' + str(len(connection['nodes'])))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('Projects access check failed; private details suppressed')
        raise SystemExit(1)
