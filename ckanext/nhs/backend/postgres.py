# -*- coding: utf-8 -*-

import logging
import sys
import sqlalchemy
import os

import sqlalchemy.engine.url as sa_url
import ckan.plugins as p

import ckan.lib.cli as cli
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.lib.lazyjson import LazyJSONObject

import ckanext.datastore.helpers as datastore_helpers
import ckanext.nhs.interfaces as interfaces
import ckanext.datastore.interfaces as datastore_interfaces



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
from ckanext.datastore.backend.postgres import DatastorePostgresqlBackend

if not os.environ.get('DATASTORE_LOAD'):
    ValidationError = toolkit.ValidationError
else:
    log.warn("Running datastore without CKAN")

    class ValidationError(Exception):
        def __init__(self, error_dict):
            pprint.pprint(error_dict)

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


def nhs_search_data(context, data_dict):
    print 'NHS search data'
    datastore_db.validate(context, data_dict)
    fields_types = datastore_db._get_fields_types(context, data_dict)
    print fields_types

    query_dict = {
        'select': [],
        'sort': [],
        'where': []
    }

    for plugin in p.PluginImplementations(interfaces.INHSDatastore):
        query_dict = plugin.nhs_datastore_search(context, data_dict,
                                             fields_types, query_dict)
        print 'rerurned query'
        print query_dict

    where_clause, where_values = datastore_db._where(query_dict['where'])

    # FIXME: Remove duplicates on select columns
    print query_dict['group_by']
    select_columns = ', '.join(query_dict['select']).replace('%', '%%')
    #ts_query = query_dict['ts_query'].replace('%', '%%')
    resource_id = data_dict['resource_id'].replace('%', '%%')
    sort = query_dict['sort']
    limit = query_dict['limit']
    offset = query_dict['offset']
    group_by = query_dict['group_by']
    print group_by

    if sort:
        sort_clause = 'ORDER BY %s' % (', '.join(sort)).replace('%', '%%')
    else:
        sort_clause = ''

    if group_by:
        group_clause = 'GROUP BY "%s"' % group_by
    else:
        group_clause = ''

    records_format = data_dict['records_format']
    if records_format == u'objects':
        sql_fmt = u'''
            SELECT array_to_json(array_agg(j))::text FROM (
                SELECT {select}
                FROM "{resource}"
                {where} {group_by} LIMIT {limit} OFFSET {offset}
            ) AS j'''
    elif records_format == u'lists':
        select_columns = u" || ',' || ".join(
            s for s in query_dict['select']
        ).replace('%', '%%')
        sql_fmt = u'''
            SELECT '[' || array_to_string(array_agg(j.v), ',') || ']' FROM (
                SELECT {distinct} '[' || {select} || ']' v
                FROM (
                    SELECT * FROM "{resource}"
                    {where} {sort} LIMIT {limit} OFFSET {offset}) as z
            ) AS j'''
    elif records_format == u'csv':
        sql_fmt = u'''
            COPY (
                SELECT {select}
                FROM "{resource}" {ts_query}
                {where} {sort} LIMIT {limit} OFFSET {offset}
            ) TO STDOUT csv DELIMITER ',' '''
    elif records_format == u'tsv':
        sql_fmt = u'''
            COPY (
                SELECT {select}
                FROM "{resource}" {ts_query}
                {where} {sort} LIMIT {limit} OFFSET {offset}
            ) TO STDOUT csv DELIMITER '\t' '''

    sql_string = sql_fmt.format(
        select=select_columns,
        resource=resource_id,
        where=where_clause,
        group_by=group_clause,
        sort=sort_clause,
        limit=limit,
        offset=offset)

    if records_format == u'csv' or records_format == u'tsv':
        buf = StringIO()
        _execute_single_statement_copy_to(
            context, sql_string, where_values, buf)
        records = buf.getvalue()
    else:
        v = list(datastore_db._execute_single_statement(
            context, sql_string, where_values))[0][0]
        if v is None:
            records = []
        else:
            records = LazyJSONObject(v)
    data_dict['records'] = records

    field_info = datastore_db._get_field_info(
        context['connection'], data_dict['resource_id'])
    result_fields = []
    for field_id, field_type in fields_types.iteritems():
        f = {u'id': field_id, u'type': field_type}
        if field_id in field_info:
            f['info'] = field_info[f['id']]
        result_fields.append(f)
    data_dict['fields'] = result_fields
    datastore_db._unrename_json_field(data_dict)

    datastore_db._insert_links(data_dict, limit, offset)

    if data_dict.get('include_total', True):
        count_sql_string = u'''SELECT count(*) FROM (
            SELECT {select}
            FROM "{resource}" {where}) as t;'''.format(
            select=select_columns,
            resource=resource_id,
            where=where_clause)
        count_result = datastore_db._execute_single_statement(
            context, count_sql_string, where_values)
        data_dict['total'] = count_result.fetchall()[0][0]

    return data_dict

def nhs_search(context, data_dict):
    backend = NHSDatastorePostgresqlBackend.get_active_backend()
    engine = backend._get_read_engine()
    context['connection'] = engine.connect()
    timeout = context.get('query_timeout', _TIMEOUT)
    datastore_db._cache_types(context)

    try:
        context['connection'].execute(
            u'SET LOCAL statement_timeout TO {0}'.format(timeout))
        return nhs_search_data(context, data_dict)
    except DBAPIError as e:
        if e.orig.pgcode == datastore_db._PG_ERR_CODE['query_canceled']:
            raise ValidationError({
                'query': ['Search took too long']
            })
        raise ValidationError({
            'query': ['Invalid query'],
            'info': {
                'statement': [e.statement],
                'params': [e.params],
                'orig': [str(e.orig)]
            }
        })
    finally:
        context['connection'].close()

def _where_clauses(data_dict, fields_types):
    filters = data_dict.get('filters', {})
    clauses = []

    for field, value in filters.iteritems():
        if field not in fields_types:
            continue
        field_array_type = datastore_db._is_array_type(fields_types[field])
        if isinstance(value, list) and not field_array_type:
            clause_str = (u'"{0}" in ({1})'.format(field,
                          ','.join(['%s'] * len(value))))
            clause = (clause_str,) + tuple(value)
        else:
            clause = (u'"{0}" = %s'.format(field), value)
        clauses.append(clause)

    return clauses


class NHSDatastorePostgresqlBackend(DatastorePostgresqlBackend):

    def _get_write_engine(self):
        return datastore_db._get_engine_from_url(self.write_url)

    def _get_read_engine(self):
        return datastore_db._get_engine_from_url(self.read_url)

    def _log_or_raise(self, message):
        if self.config.get('debug'):
            log.critical(message)
        else:
            raise DatastoreException(message)

    def _check_urls_and_permissions(self):
        # Make sure that the right permissions are set
        # so that no harmful queries can be made

        if self._same_ckan_and_datastore_db():
            self._log_or_raise(
                'CKAN and DataStore database cannot be the same.')

        if self._same_read_and_write_url():
            self._log_or_raise('The write and read-only database '
                               'connection urls are the same.')

        if not self._read_connection_has_correct_privileges():
            self._log_or_raise('The read-only user has write privileges.')

    def _is_read_only_database(self):
        ''' Returns True if no connection has CREATE privileges on the public
        schema. This is the case if replication is enabled.'''
        for url in [self.ckan_url, self.write_url, self.read_url]:
            connection = datastore_db._get_engine_from_url(url).connect()
            try:
                sql = u"SELECT has_schema_privilege('public', 'CREATE')"
                is_writable = connection.execute(sql).first()[0]
            finally:
                connection.close()
            if is_writable:
                return False
        return True

    def _same_ckan_and_datastore_db(self):
        '''Returns True if the CKAN and DataStore db are the same'''
        return self._get_db_from_url(self.ckan_url) == self._get_db_from_url(
            self.read_url)

    def _get_db_from_url(self, url):
        db_url = sa_url.make_url(url)
        return db_url.host, db_url.port, db_url.database

    def _same_read_and_write_url(self):
        return self.write_url == self.read_url

    def _read_connection_has_correct_privileges(self):
        ''' Returns True if the right permissions are set for the read
        only user. A table is created by the write user to test the
        read only user.
        '''
        write_connection = self._get_write_engine().connect()
        read_connection_user = sa_url.make_url(self.read_url).username

        drop_foo_sql = u'DROP TABLE IF EXISTS _foo'

        write_connection.execute(drop_foo_sql)

        try:
            write_connection.execute(u'CREATE TEMP TABLE _foo ()')
            for privilege in ['INSERT', 'UPDATE', 'DELETE']:
                privilege_sql = u"SELECT has_table_privilege(%s, '_foo', %s)"
                have_privilege = write_connection.execute(
                    privilege_sql,
                    (read_connection_user, privilege)
                ).first()[0]
                if have_privilege:
                    return False
        finally:
            write_connection.execute(drop_foo_sql)
            write_connection.close()
        return True

    def configure(self, config):
        self.config = config
        # check for ckan.datastore.write_url and ckan.datastore.read_url
        if ('ckan.datastore.write_url' not in config):
            error_msg = 'ckan.datastore.write_url not found in config'
            raise DatastoreException(error_msg)
        if ('ckan.datastore.read_url' not in config):
            error_msg = 'ckan.datastore.read_url not found in config'
            raise DatastoreException(error_msg)

        # Check whether users have disabled datastore_search_sql
        self.enable_sql_search = toolkit.asbool(
            self.config.get('ckan.datastore.sqlsearch.enabled', True))

        # Check whether we are running one of the paster commands which means
        # that we should ignore the following tests.
        args = sys.argv
        if args[0].split('/')[-1] == 'paster' and 'datastore' in args[1:]:
            log.warn('Omitting permission checks because you are '
                     'running paster commands.')
            return

        self.ckan_url = self.config['sqlalchemy.url']
        self.write_url = self.config['ckan.datastore.write_url']
        self.read_url = self.config['ckan.datastore.read_url']

        self.read_engine = self._get_read_engine()
        if not model.engine_is_pg(self.read_engine):
            log.warn('We detected that you do not use a PostgreSQL '
                     'database. The DataStore will NOT work and DataStore '
                     'tests will be skipped.')
            return

        if self._is_read_only_database():
            log.warn('We detected that CKAN is running on a read '
                     'only database. Permission checks and the creation '
                     'of _table_metadata are skipped.')
        else:
            self._check_urls_and_permissions()

    def nhs_datastore_search(self, context, data_dict, fields_types, query_dict):
        print 'WE ARE IN THE PLUGIN'

        fields = data_dict.get('fields')

        if fields:
            field_ids = datastore_helpers.get_list(fields)
        else:
            field_ids = fields_types.keys()

        limit = data_dict.get('limit', 100)
        offset = data_dict.get('offset', 0)
        group_by = data_dict.get('sort', '')
        print group_by

        sort = datastore_db._sort(data_dict, fields_types)
        where = _where_clauses(data_dict, fields_types)

        select_cols = []
        records_format = data_dict.get(u'records_format')
        for field_id in field_ids:
            fmt = u'to_json({0})' if records_format == u'lists' else u'{0}'
            typ = fields_types.get(field_id)
            if typ == u'nested':
                fmt = u'({0}).json'
            elif typ == u'timestamp':
                fmt = u"to_char({0}, 'YYYY-MM-DD\"T\"HH24:MI:SS')"
                if records_format == u'lists':
                    fmt = u"to_json({0})".format(fmt)
            elif typ.startswith(u'_') or typ.endswith(u'[]'):
                fmt = u'array_to_json({0})'
            if records_format == u'objects':
                fmt += u' as {0}'
            select_cols.append(fmt.format(
                datastore_db.identifier(field_id)))

        print query_dict

        #query_dict['distinct'] = data_dict.get('distinct', False)
        query_dict['select'] += select_cols
        print group_by
        query_dict['group_by'] = group_by
        query_dict['sort'] += sort
        query_dict['where'] += where
        query_dict['limit'] = limit
        query_dict['offset'] = offset
        
        print 'some query'
        print query_dict

        return query_dict

