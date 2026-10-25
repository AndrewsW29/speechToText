// Collection-level pre-request script:
//  1. tags every request with an X-Correlation-ID (shows up in the API's JSON logs);
//  2. when auth is enabled, obtains a Keycloak access token (password grant, or client credentials
//     when `clientSecret` is set) and refreshes it shortly before it expires.
pm.request.headers.upsert({ key: 'X-Correlation-ID', value: pm.variables.replaceIn('{{$guid}}') });

const authEnabled = (pm.variables.get('authEnabled') || 'true') !== 'false';
const noAuthRequest = pm.request.auth && pm.request.auth.type === 'noauth';
if (!authEnabled || noAuthRequest) {
  return;
}

const supplied = pm.environment.get('accessToken');
const expiresAt = Number(pm.environment.get('tokenExpiresAt') || 0);
if (supplied && (!expiresAt || Date.now() < expiresAt - 30000)) {
  return; // a pasted token, or a fetched one that is still valid
}

const keycloak = pm.environment.get('keycloakUrl');
const realm = pm.environment.get('realm');
const clientId = pm.environment.get('clientId');
const clientSecret = pm.environment.get('clientSecret');
const username = pm.environment.get('username');
const password = pm.environment.get('password');
if (!keycloak || !realm || !clientId || !((username && password) || clientSecret)) {
  console.warn('No token and no Keycloak credentials: set accessToken, or username/password, in the environment.');
  return;
}

const form = clientSecret
  ? [
      { key: 'grant_type', value: 'client_credentials' },
      { key: 'client_id', value: clientId },
      { key: 'client_secret', value: clientSecret },
    ]
  : [
      { key: 'grant_type', value: 'password' },
      { key: 'client_id', value: clientId },
      { key: 'username', value: username },
      { key: 'password', value: password },
    ];

pm.sendRequest(
  {
    url: `${keycloak}/realms/${realm}/protocol/openid-connect/token`,
    method: 'POST',
    header: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: { mode: 'urlencoded', urlencoded: form },
  },
  (error, response) => {
    if (error || response.code !== 200) {
      console.error('Keycloak token request failed', error || response.code);
      return;
    }
    const data = response.json();
    pm.environment.set('accessToken', data.access_token);
    pm.environment.set('tokenExpiresAt', String(Date.now() + data.expires_in * 1000));
  },
);
