"""External Storage API actions
"""
import ast

from ckan.plugins import toolkit
from ckan.common import config, request
import ckan.logic as logic
_check_access = logic.check_access
import json

import datetime
import logging
log = logging.getLogger(__name__)
import subprocess

@toolkit.side_effect_free
def get_cloud_egress(context, data_dict):
    log.debug(data_dict)
    _check_access('egress_gcp_fetch',context,data_dict)
    if ('start_time' and 'end_time') not in data_dict:
        return u'Please provide start_time and endtime'
    start_time = data_dict.get('start_time')
    end_time = data_dict.get('end_time')
    result = subprocess.check_output(['python3', '/srv/app/gcp_storage_egress.py',start_time,end_time])
    return result.strip()