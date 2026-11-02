"""Tests for plugin.py."""
import logging

import flask

import ckanext.nhs.plugin as plugin


def test_plugin():
    pass


class TestResolveIdentity:
    def test_token_with_known_user(self):
        assert plugin._resolve_identity("kate", True) == ("kate", "token")

    def test_token_with_unresolved_user(self):
        # Authorization header present but CKAN couldn't map it to a user
        # (invalid/revoked token) - still worth flagging as token traffic.
        assert plugin._resolve_identity(None, True) == ("unknown", "token")
        assert plugin._resolve_identity("", True) == ("unknown", "token")

    def test_session_login(self):
        assert plugin._resolve_identity("kate", False) == ("kate", "session")

    def test_anonymous(self):
        assert plugin._resolve_identity(None, False) == ("anonymous", "anonymous")
        assert plugin._resolve_identity("", False) == ("anonymous", "anonymous")


class TestIsStaticAsset:
    def test_known_prefixes(self):
        assert plugin._is_static_asset("/base/images/ckan.ico")
        assert plugin._is_static_asset("/webassets/base/51d427fe_main.css")
        assert plugin._is_static_asset("/fanstatic/js/nhs.js")
        assert plugin._is_static_asset("/images/nhs-logo-new.png")

    def test_suffix_fallback_for_unprefixed_static_files(self):
        # e.g. https://ckan.nhs.staging.datopian.com/restricted_theme.css
        assert plugin._is_static_asset("/restricted_theme.css")

    def test_real_pages_and_api_calls_are_not_static(self):
        assert not plugin._is_static_asset("/dataset/some-dataset")
        assert not plugin._is_static_asset("/api/3/action/package_search")
        assert not plugin._is_static_asset("/api/extract-users")


class TestLogRequestIdentity:
    """Exercises the real after_request hook against a plain Flask app.

    ckan.common.g/request proxy to flask.g/flask.request for whichever
    Flask app/request context is currently active, so this doesn't need a
    full CKAN app to prove the hook itself works.
    """

    def _make_app(self):
        app = flask.Flask(__name__)
        app.after_request(plugin._log_request_identity)

        @app.route("/ping")
        def ping():
            flask.g.user = flask.request.args.get("as_user") or None
            return "pong"

        @app.route("/webassets/base/main.css")
        def asset():
            flask.g.user = None
            return "body { color: red }"

        return app

    def test_token_request_is_logged(self, caplog):
        app = self._make_app()
        with caplog.at_level(logging.INFO, logger="ckanext.nhs.access"):
            resp = app.test_client().get(
                "/ping?as_user=kate", headers={"Authorization": "sometoken"}
            )

        assert resp.status_code == 200
        assert resp.data == b"pong"
        assert "identity=kate" in caplog.text
        assert "auth_method=token" in caplog.text

    def test_anonymous_request_is_logged(self, caplog):
        app = self._make_app()
        with caplog.at_level(logging.INFO, logger="ckanext.nhs.access"):
            resp = app.test_client().get("/ping")

        assert resp.status_code == 200
        assert "identity=anonymous" in caplog.text
        assert "auth_method=anonymous" in caplog.text

    def test_static_asset_request_is_not_logged(self, caplog):
        app = self._make_app()
        with caplog.at_level(logging.INFO, logger="ckanext.nhs.access"):
            resp = app.test_client().get("/webassets/base/main.css")

        assert resp.status_code == 200
        assert caplog.text == ""

    def test_logging_failure_does_not_break_the_response(self, caplog, monkeypatch):
        monkeypatch.setattr(
            plugin,
            "_resolve_identity",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        app = self._make_app()
        with caplog.at_level(logging.INFO):
            resp = app.test_client().get("/ping")

        assert resp.status_code == 200
        assert resp.data == b"pong"
