import logging
from unittest.mock import Mock

import pytest
from flask import Flask, g

from ckanext.nhs.following import follow_group


def test_follow_group_preserves_result_and_arguments(caplog):
    context = {"user": "test-user"}
    data_dict = {"id": "test-group", "token": "secret-data-token"}
    result = {"id": "test-group"}
    original_action = Mock(return_value=result)

    with caplog.at_level(logging.INFO):
        assert follow_group(original_action, context, data_dict) is result

    original_action.assert_called_once_with(context, data_dict)
    assert "NHS follow_group started" in caplog.text
    assert "NHS follow_group succeeded" in caplog.text
    assert "secret-data-token" not in caplog.text


def test_follow_group_logs_request_and_reraises(caplog):
    app = Flask(__name__)
    error = RuntimeError("authorization failed")
    original_action = Mock(side_effect=error)

    with app.test_request_context(
        "/organization/follow/test-group?token=secret-query-token",
        method="POST",
        headers={"Cookie": "ckan=secret-cookie", "X-CSRFToken": "secret-csrf"},
    ):
        g.userobj = Mock(id="test-user-id", sysadmin=False)
        with caplog.at_level(logging.INFO), pytest.raises(RuntimeError) as exc:
            follow_group(original_action, {}, {"id": "test-group"})

    assert exc.value is error
    assert "NHS follow_group failed" in caplog.text
    assert "test-user-id" in caplog.text
    assert "/organization/follow/test-group" in caplog.text
    assert "Traceback" in caplog.text
    assert "NHS follow_group succeeded" not in caplog.text
    for secret in ("secret-query-token", "secret-cookie", "secret-csrf"):
        assert secret not in caplog.text
