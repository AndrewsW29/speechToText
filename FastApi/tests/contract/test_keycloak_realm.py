import json
from pathlib import Path

REALM = Path(__file__).resolve().parents[2] / "deploy" / "docker" / "keycloak" / "realm.json"
DATA = json.loads(REALM.read_text())


def test_ingest_role_and_dev_users_exist() -> None:
    assert "ingest" in {r["name"] for r in DATA["roles"]["realm"]}
    users = {u["username"]: u for u in DATA["users"]}
    assert set(users) >= {"dev-user", "dev-ingester"}
    assert (
        "ingest" in users["dev-ingester"]["realmRoles"]
        and "ingest" not in users["dev-user"]["realmRoles"]
    )


def test_passwords_come_from_environment_placeholders_never_literals() -> None:
    for user in DATA["users"]:
        for credential in user["credentials"]:
            assert credential["value"].startswith("${") and credential["value"].endswith("}"), user[
                "username"
            ]


def test_postman_client_allows_the_password_grant_and_adds_the_api_audience() -> None:
    client = next(c for c in DATA["clients"] if c["clientId"] == "voice-postman")
    assert client["publicClient"] is True and client["directAccessGrantsEnabled"] is True
    mapper = next(
        m for m in client["protocolMappers"] if m["protocolMapper"] == "oidc-audience-mapper"
    )
    assert mapper["config"]["included.client.audience"] == "voice-api"
    assert "dev" in client["attributes"]["description"].lower()
