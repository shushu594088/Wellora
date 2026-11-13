"""Exercise the deployed HTTP API with PostgreSQL; use only on a fresh test DB.

Run prepare, restart both containers, run verify, then always run cleanup.
State stays in the API container's /tmp with mode 600; no tokens are printed.
"""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import delete, func, select

from app import Account, LoginThrottle, SessionLocal, digest_token

STATE = Path('/tmp/wellora-deployment-smoke.json')
BASE = 'http://127.0.0.1:8000/api/v1'


def request(method, path, body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = json.dumps(body).encode() if body is not None else None
    try:
        response = urlopen(Request(BASE + path, data=data, headers=headers, method=method), timeout=30)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        return response.code, json.loads(raw) if raw else None


def check(label, actual, expected):
    if actual != expected:
        raise AssertionError(f'{label}: expected {expected!r}, got {actual!r}')
    print(label + '=PASS', flush=True)


def wait_for_health(attempts=30):
    expected = (200, {'status': 'ok'})
    for attempt in range(attempts):
        try:
            result = request('GET', '/health')
            if result == expected:
                return result
        except URLError:
            pass
        if attempt + 1 < attempts:
            time.sleep(1)
    raise RuntimeError('API did not become healthy after restart')


def prepare():
    if STATE.exists():
        raise RuntimeError('Clean up the existing smoke fixture before running again')
    with SessionLocal() as db:
        check('FRESH_POSTGRES_DATABASE', db.scalar(select(func.count()).select_from(Account)), 0)
    prefix = 'smoke_' + secrets.token_hex(5) + '_'
    state = {'prefix': prefix, 'password': secrets.token_urlsafe(24), 'usernames': [prefix + str(i) for i in range(21)]}
    with os.fdopen(os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as stream:
        json.dump(state, stream)

    def register(username):
        return request('POST', '/auth/register', {'username': username, 'password': state['password']})[0]

    def login(username):
        code, result = request('POST', '/auth/login', {'username': username, 'password': state['password']})
        check('LOGIN', code, 200)
        return result['access_token']

    check('HEALTH', request('GET', '/health'), (200, {'status': 'ok'}))
    check('REGISTER_A', register(state['usernames'][0]), 201)
    check('REGISTER_B', register(state['usernames'][1]), 201)
    a, b = login(state['usernames'][0]), login(state['usernames'][1])
    code, profile = request('POST', '/profiles', {'display_name': 'Fictional deployment fixture', 'birth_date': '1980-01-01'}, a)
    check('CREATE_PROFILE', code, 201)
    path = '/profiles/' + profile['profile_id']
    check('OTHER_ACCOUNT_READ', request('GET', path, token=b)[0], 404)
    check('OTHER_ACCOUNT_UPDATE', request('PATCH', path, {'display_name': 'Forbidden', 'version': 1}, b)[0], 404)
    check('OTHER_ACCOUNT_LIST', request('GET', '/profiles', token=b)[1]['items'], [])
    code, updated = request('PATCH', path, {'display_name': 'Updated fictional fixture', 'birth_date': '1980-01-01', 'version': 1}, a)
    check('UPDATE_PROFILE', (code, updated['version']), (200, 2))
    check('STALE_VERSION', request('PATCH', path, {'display_name': 'Stale fixture', 'version': 1}, a)[0], 409)
    check('LOGOUT', request('POST', '/auth/logout', token=b)[0], 204)
    check('REVOKED_SESSION', request('GET', '/profiles', token=b)[0], 401)
    for username in state['usernames'][2:19]:
        if register(username) != 201:
            raise AssertionError('Could not fill fixture accounts')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = sorted(pool.map(register, state['usernames'][19:21]))
    check('CONCURRENT_LAST_ACCOUNT_SLOT', results, [201, 429])
    with SessionLocal() as db:
        check('ACCOUNT_LIMIT', db.scalar(select(func.count()).select_from(Account)), 20)
    state.update(token=a, revoked_token=b, profile_path=path)
    STATE.write_text(json.dumps(state), encoding='utf-8')
    print('PREPARED_FOR_CONTAINER_RESTART', flush=True)


def verify():
    state = json.loads(STATE.read_text(encoding='utf-8'))
    check('POST_RESTART_HEALTH', wait_for_health(), (200, {'status': 'ok'}))
    code, profile = request('GET', state['profile_path'], token=state['token'])
    check('POST_RESTART_PROFILE', (code, profile['display_name'], profile['version'], profile['birth_date']),
          (200, 'Updated fictional fixture', 2, '1980-01-01'))
    check('POST_RESTART_REVOCATION', request('GET', '/profiles', token=state['revoked_token'])[0], 401)
    with SessionLocal() as db:
        check('POST_RESTART_ACCOUNT_COUNT', db.scalar(select(func.count()).select_from(Account)), 20)


def cleanup():
    if not STATE.exists():
        print('NO_FIXTURE_STATE', flush=True)
        return
    state = json.loads(STATE.read_text(encoding='utf-8'))
    with SessionLocal() as db:
        db.execute(delete(Account).where(Account.username.in_(state['usernames'])))
        keys = [digest_token('username:' + username) for username in state['usernames']]
        keys.append(digest_token('ip:127.0.0.1'))
        db.execute(delete(LoginThrottle).where(LoginThrottle.key.in_(keys)))
        db.commit()
        check('FIXTURE_ACCOUNTS_REMOVED', db.scalar(select(func.count()).select_from(Account)), 0)
    STATE.unlink()
    print('FIXTURE_STATE_REMOVED', flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify, 'cleanup': cleanup}[sys.argv[1]]()
