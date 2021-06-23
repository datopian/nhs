"""External Storage API actions
"""
import ast

from ckan.plugins import toolkit
from ckan.common import config, request


import datetime
import logging
log = logging.getLogger(__name__)
import subprocess
@toolkit.side_effect_free
def get_cloud_egress(context, data_dict):
    res = subprocess.check_output(['python3', '/srv/app/gcp_storage_egress.py'])
    return res