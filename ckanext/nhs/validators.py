import ckan.plugins.toolkit as toolkit

import logging as log

log = log.getLogger(__name__)



def upload_to_datastore(key, data, errors, context):
    return data.get(('upload_to_bigquery',), True)

