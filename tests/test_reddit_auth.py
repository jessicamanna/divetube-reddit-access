import pytest

import pipeline.reddit_auth as reddit_auth
from pipeline.reddit_auth import deleted_ids, fetch_info, get_app_token


class FakeResponse:
    def __init__(self, body):
        self._body = body
        self.status_code = 200

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def get(self, url, params=None, **kwargs):
        call = {**(params or {}), **kwargs}
        self.calls.append(call)
        return FakeResponse(self.handler(call))

    def post(self, url, data=None, auth=None, **kwargs):
        call = {"data": data, "auth": auth}
        self.calls.append(call)
        return FakeResponse(self.handler(call))


def test_deleted_ids():
    info = {"t1_a": {"author": "x", "body": "fine"}, "t1_b": {"author": "[deleted]", "body": "x"},
            "t1_c": {"author": "y", "body": "[removed]"}}
    assert deleted_ids(["t1_a", "t1_b", "t1_c", "t1_d"], info) == {"t1_b", "t1_c", "t1_d"}


def test_fetch_info_batches_by_100():
    s = FakeSession(lambda p: {"data": {"children": [{"data": {"name": n}} for n in p["id"].split(",")]}})
    out = fetch_info([f"t1_{i}" for i in range(230)], "tok", s, sleep=lambda _: None)
    assert len(out) == 230 and [len(c["id"].split(",")) for c in s.calls] == [100, 100, 30]


def test_token_request():
    s = FakeSession(lambda p: {"access_token": "tok", "expires_in": 86400})
    assert get_app_token("id", "secret", s) == "tok"
    assert s.calls[0]["data"]["grant_type"] == "client_credentials" and s.calls[0]["auth"] == ("id", "secret")


def test_fetch_info_uses_only_the_oauth_host_with_a_token():
    urls = []

    class S(FakeSession):
        def get(self, url, params=None, **kwargs):
            urls.append(url)
            return super().get(url, params, **kwargs)

    s = S(lambda p: {"data": {"children": [{"data": {"name": n}} for n in p["id"].split(",")]}})
    fetch_info([f"t1_{i}" for i in range(150)], "tok", s, sleep=lambda _: None)
    assert urls == ["https://oauth.reddit.com/api/info"] * 2
    assert s.calls[0]["headers"]["Authorization"] == "bearer tok"


@pytest.mark.parametrize("token", [None, ""])
def test_fetch_info_refuses_without_a_token(token):
    s = FakeSession(lambda p: {})
    with pytest.raises(ValueError):
        fetch_info(["t1_a"], token, s, sleep=lambda _: None)
    assert s.calls == []


def test_no_public_endpoint_left():
    assert not hasattr(reddit_auth, "PUBLIC_INFO_URL") and not hasattr(reddit_auth, "PUBLIC_DELAY_S")


@pytest.mark.parametrize("env", [{}, {"REDDIT_CLIENT_ID": "id"}, {"REDDIT_CLIENT_SECRET": "secret"}])
def test_main_without_credentials_sends_nothing_and_writes_nothing(env, monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    for k, val in env.items():
        monkeypatch.setenv(k, val)
    (tmp_path / "deleted.json").write_text('["t1_old"]')
    monkeypatch.setattr(reddit_auth, "WORK", tmp_path)
    session = FakeSession(lambda p: {})
    monkeypatch.setattr(reddit_auth.requests, "Session", lambda: session)
    assert reddit_auth.main([]) == 0
    assert session.calls == []
    assert (tmp_path / "deleted.json").read_text() == '["t1_old"]'
    assert "No request sent to Reddit." in capsys.readouterr().out


def test_fetch_info_fails_loudly_on_http_error():
    class S(FakeSession):
        def get(self, url, params=None, **kwargs):
            resp = FakeResponse({})
            resp.status_code = 429
            return resp

    with pytest.raises(RuntimeError):
        fetch_info(["t1_a"], "tok", S(lambda p: {}), sleep=lambda _: None)
