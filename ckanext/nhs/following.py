"""Diagnostic logging for group, theme and organization follow requests."""

import logging
from uuid import uuid4

from flask import has_request_context, request
import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


@toolkit.chained_action
def follow_group(original_action, context, data_dict):
    # Only allowlisted diagnostic fields: never log headers, cookies, tokens,
    # the full context/data_dict, or query strings.
    diagnostic = {
        "diagnostic_id": uuid4().hex,
        "target_id": data_dict.get("id"),
        "context_user": context.get("user"),
        "ignore_auth": context.get("ignore_auth", False),
    }
    if has_request_context():
        user = getattr(toolkit.g, "userobj", None)
        view_args = request.view_args or {}
        diagnostic.update({
            "user_id": getattr(user, "id", None),
            "sysadmin": getattr(user, "sysadmin", False),
            "method": request.method,
            "path": request.path,
            "endpoint": request.endpoint,
            "group_type": view_args.get("group_type"),
            "is_organization": view_args.get("is_organization"),
        })

    log.info("NHS follow_group started: %r", diagnostic)
    try:
        result = original_action(context, data_dict)
    except Exception:
        log.exception("NHS follow_group failed: %r", diagnostic)
        raise
    log.info("NHS follow_group succeeded: %r", diagnostic)
    return result
