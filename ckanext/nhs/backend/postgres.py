# -*- coding: utf-8 -*-

import logging
import sys
import sqlalchemy

import sqlalchemy.engine.url as sa_url

import ckan.plugins.toolkit as toolkit
from sqlalchemy.exc import (ProgrammingError, IntegrityError,
                            DBAPIError, DataError)

import ckan.model as model
from ckan.common import config, OrderedDict

from ckanext.datastore.backend import (
    DatastoreBackend,
    DatastoreException,
    _parse_sort_clause
)
from ckanext.datastore.backend import InvalidDataError
import ckanext.datastore.helpers as datastore_helpers
import ckanext.datastore.backend.postgres as datastore_db

log = logging.getLogger(__name__)

_pg_types = {}
_type_names = set()
_engines = {}

_TIMEOUT = 60000  # milliseconds


def get_fulltext_enable():
    fulltext_enable = config.get('ckanext.xloader.enable_fulltext')
    if fulltext_enable is None:
        fulltext_enable = False
    return fulltext_enable


def create_indexes(context, data_dict):
    connection = context['connection']
    indexes = datastore_helpers.get_list(data_dict.get('indexes'))
    # primary key is not a real primary key
    # it's just a unique key
    primary_key = datastore_helpers.get_list(data_dict.get('primary_key'))

    sql_index_tmpl = u'CREATE {unique} INDEX "{name}" ON "{res_id}"'
    sql_index_string_method = sql_index_tmpl + u' USING {method}({fields})'
    sql_index_string = sql_index_tmpl + u' ({fields})'
    sql_index_strings = []

    fields = datastore_db._get_fields(context, data_dict)
    field_ids = datastore_db._pluck('id', fields)
    json_fields = [x['id'] for x in fields if x['type'] == 'nested']

    if indexes is not None:
        datastore_db._drop_indexes(context, data_dict, False)
    else:
        indexes = []

    if primary_key is not None:
        unique_keys = _get_unique_key(context, data_dict)
        if sorted(unique_keys) != sorted(primary_key):
            datastore_db._drop_indexes(context, data_dict, True)
            indexes.append(primary_key)

    for index in indexes:
        if not index:
            continue

        index_fields = datastore_helpers.helpers.datastore_helpers.get_list(index)
        for field in index_fields:
            if field not in field_ids:
                raise ValidationError({
                    'index': [
                        u'The field "{0}" is not a valid column name.'.format(
                            index)]
                })
        fields_string = u', '.join(
            ['(("{0}").json::text)'.format(field)
                if field in json_fields else
                '"%s"' % field
                for field in index_fields])
        sql_index_strings.append(sql_index_string.format(
            res_id=data_dict['resource_id'],
            unique='unique' if index == primary_key else '',
            name=_generate_index_name(data_dict['resource_id'], fields_string),
            fields=fields_string))

    sql_index_strings = map(lambda x: x.replace('%', '%%'), sql_index_strings)
    current_indexes = datastore_db._get_index_names(context['connection'],
                                       data_dict['resource_id'])
    for sql_index_string in sql_index_strings:
        has_index = [c for c in current_indexes
                     if sql_index_string.find(c) != -1]
        if not has_index:
            connection.execute(sql_index_string)


class NHSDatastorePostgresqlBackend(DatastoreBackend):
    pass

