"""Test doubles for HTTP sessions."""


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, payload=None, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.content = b""

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    """Serve scripted responses (or raise scripted exceptions) in order, recording calls."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
