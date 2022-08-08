"""External Storage API actions
"""
import ast

from ckan.plugins import toolkit
from ckan.common import config, request
import ckan.logic as logic
_check_access = logic.check_access
import json, ast
from datetime import datetime
import time
#import datetime
import logging
log = logging.getLogger(__name__)
import subprocess

def date_validator(date):
    format = "%d/%m/%Y"
    try:
        datetime.strptime(date, format)
        return True
    except ValueError:
        return None


@toolkit.side_effect_free
def get_cloud_egress(context, data_dict):
    '''
    Fetches egress data from gcp
    '''
    # Checks
    _check_access('egress_gcp_fetch',context,data_dict)
    if ('start_time' and 'end_time') not in data_dict:
        return u'Please provide start_time and endtime'

    start_time = data_dict.get('start_time')
    end_time = data_dict.get('end_time')

    start_valid = date_validator(start_time)
    end_valid = date_validator(end_time)

    if not (start_valid and end_valid):
        return u'Please provide a valid date in format DD/MM/YY'
    logging.error(start_time)
    logging.error(end_time)

    result = subprocess.check_output(['python3', '/srv/app/gcp_storage_egress.py',start_time,end_time])
    result = ast.literal_eval(result)
    return {'data': result}