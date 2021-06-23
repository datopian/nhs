"""External Storage API actions
"""
import ast

from ckan.plugins import toolkit
from ckan.common import config, request
import ckan.logic as logic
_check_access = logic.check_access

import datetime
import logging
log = logging.getLogger(__name__)
import subprocess
@toolkit.side_effect_free
def get_cloud_egress(context, data_dict):
    log.debug(data_dict)
    _check_access('egress_gcp_fetch',context,data_dict)
    res = subprocess.check_output(['python3', '/srv/app/gcp_storage_egress.py'])
    return res