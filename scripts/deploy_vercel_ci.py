"""Deploy using private Actions credentials, without tokens in command arguments."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit


def main():
    required = ('VERCEL_TOKEN', 'VERCEL_ORG_ID', 'VERCEL_PROJECT_ID')
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise SystemExit('Add these GitHub Actions secrets: ' + ', '.join(missing))
    target = os.environ.get('DEPLOY_TARGET', 'preview')
    if target not in ('preview', 'production'):
        raise SystemExit('DEPLOY_TARGET must be preview or production')
    # The target must be explicitly identified; never create/link an arbitrary app.
    org_id = os.environ['VERCEL_ORG_ID']
    project_id = os.environ['VERCEL_PROJECT_ID']
    if not org_id.startswith('team_') or not project_id.startswith('prj_'):
        raise SystemExit('Use the actual Team ID (team_) and Project ID (prj_), not their names')
    project = Path('.vercel')
    project.mkdir(exist_ok=True)
    (project / 'project.json').write_text(json.dumps({
        'orgId': org_id, 'projectId': project_id, 'projectName': 'fitness-ai'
    }))
    child_env = os.environ.copy()
    token = child_env.pop('VERCEL_TOKEN')
    child_env['VERCEL_TELEMETRY_DISABLED'] = '1'
    child_env['NO_COLOR'] = '1'
    with tempfile.TemporaryDirectory(prefix='fitness-vercel-auth-') as folder:
        auth = Path(folder) / 'auth.json'
        # Outside the repository/deployment bundle, private to this runner user.
        with auth.open('x', opener=lambda p, flags: os.open(p, flags, 0o600)) as handle:
            json.dump({'token': token}, handle)
        def run(*args, capture=False):
            return subprocess.run(
                ['vercel', *args, '--global-config', folder],
                check=True, env=child_env, text=True,
                stdout=subprocess.PIPE if capture else None,
            )
        run('pull', '--yes', '--environment', target)
        production = ['--prod'] if target == 'production' else []
        run('build', *production)
        result = run('deploy', '--prebuilt', '--yes', *production, capture=True)
        url = result.stdout.strip().splitlines()[-1]
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or not parsed.hostname.endswith('.vercel.app'):
            raise SystemExit('Deployment command completed; inspect Vercel for its URL')
        print('Deployment URL: ' + url)
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary:
            with open(summary, 'a') as handle:
                handle.write(f'Fitness AI {target} deployment: [{url}]({url})\n\n'
                             'Build/deployment completed. Database migration and runtime checks '
                             'must also pass before participant collection.\n')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError:
        raise SystemExit('Vercel command failed; check the preceding build or authorization error')
