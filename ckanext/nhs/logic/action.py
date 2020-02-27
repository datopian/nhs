# encoding: utf-8

import logging
import json

import sqlalchemy
from six import text_type

import ckan.lib.search as search
import ckan.lib.navl.dictization_functions
import ckan.logic as logic
import ckan.plugins as p
from ckan.common import config
import ckanext.datastore.logic.schema as dsschema
import ckanext.datastore.helpers as datastore_helpers
from ckanext.datastore.backend import (
    DatastoreBackend, InvalidDataError
)
from ckanext.datastore.backend.postgres import identifier
import ckanext.nhs.backend as nhs_backend

log = logging.getLogger(__name__)
_get_or_bust = logic.get_or_bust
_validate = ckan.lib.navl.dictization_functions.validate

WHITELISTED_RESOURCES = ['_table_metadata']

@logic.side_effect_free
def nhs_datastore_search(context, data_dict):
    '''Search a DataStore resource.

    The datastore_search action allows you to search data in a resource.
    DataStore resources that belong to private CKAN resource can only be
    read by you if you have access to the CKAN resource and send the
    appropriate authorization.

    :param resource_id: id or alias of the resource to be searched against
    :type resource_id: string
    :param filters: matching conditions to select, e.g
                    {"key1": "a", "key2": "b"} (optional)
    :type filters: dictionary
    :param q: full text query. If it's a string, it'll search on all fields on
              each row. If it's a dictionary as {"key1": "a", "key2": "b"},
              it'll search on each specific field (optional)
    :type q: string or dictionary
    :param distinct: return only distinct rows (optional, default: false)
    :type distinct: bool
    :param plain: treat as plain text query (optional, default: true)
    :type plain: bool
    :param language: language of the full text query
                     (optional, default: english)
    :type language: string
    :param limit: maximum number of rows to return (optional, default: 100)
    :type limit: int
    :param offset: offset this number of rows (optional)
    :type offset: int
    :param fields: fields to return
                   (optional, default: all fields in original order)
    :type fields: list or comma separated string
    :param sort: comma separated field names with ordering
                 e.g.: "fieldname1, fieldname2 desc"
    :type sort: string
    :param include_total: True to return total matching record count
                          (optional, default: true)
    :type include_total: bool
    :param records_format: the format for the records return value:
        'objects' (default) list of {fieldname1: value1, ...} dicts,
        'lists' list of [value1, value2, ...] lists,
        'csv' string containing comma-separated values with no header,
        'tsv' string containing tab-separated values with no header
    :type records_format: controlled list


    Setting the ``plain`` flag to false enables the entire PostgreSQL
    `full text search query language`_.

    A listing of all available resources can be found at the
    alias ``_table_metadata``.

    .. _full text search query language: http://www.postgresql.org/docs/9.1/static/datatype-textsearch.html#DATATYPE-TSQUERY

    If you need to download the full resource, read :ref:`dump`.

    **Results:**

    The result of this action is a dictionary with the following keys:

    :rtype: A dictionary with the following keys
    :param fields: fields/columns and their extra metadata
    :type fields: list of dictionaries
    :param offset: query offset value
    :type offset: int
    :param limit: query limit value
    :type limit: int
    :param filters: query filters
    :type filters: list of dictionaries
    :param total: number of total matching records
    :type total: int
    :param records: list of matching results
    :type records: depends on records_format value passed

    '''
    log.info('IN NHS datastorw search')
    backend = DatastoreBackend.get_active_backend()
    schema = context.get('schema', dsschema.datastore_search_schema())
    data_dict, errors = _validate(data_dict, schema, context)
    if errors:
        raise p.toolkit.ValidationError(errors)

    res_id = data_dict['resource_id']

    if data_dict['resource_id'] not in WHITELISTED_RESOURCES:
        res_exists, real_id = backend.resource_id_from_alias(res_id)
        # Resource only has to exist in the datastore (because it could be an
        # alias)

        if not res_exists:
            raise p.toolkit.ObjectNotFound(p.toolkit._(
                'Resource "{0}" was not found.'.format(res_id)
            ))

        # Replace potential alias with real id to simplify access checks
        if real_id:
            data_dict['resource_id'] = real_id

        p.toolkit.check_access('datastore_search', context, data_dict)

    result = nhs_backend.postgres.search(context, data_dict)
    result.pop('id', None)
    result.pop('connection_url', None)
    return result