# encoding: utf-8

import ckan.plugins.interfaces as interfaces


class INHSDatastore(interfaces.Interface):
    '''Allow modifying Datastore queries'''

    def datastore_search(self, context, data_dict, fields_types, query_dict):
        '''Modify queries made on datastore_search

        The overall design is that every IDatastore extension will receive the
        ``query_dict`` with the modifications made by previous extensions, then
        it can add/remove stuff into it before passing it on. You can think of
        it as pipes, where the ``query_dict`` is being passed to each
        IDatastore extension in the order they've been loaded allowing them to
        change the ``query_dict``. The ``datastore`` extension always comes
        first.

        The ``query_dict`` is on the form:
        {
            'select': [],
            'ts_query': '',
            'sort': [],
            'where': [],
            'limit': 100,
            'offset': 0
        }

        As extensions can both add and remove those keys, it's not guaranteed
        that any of them will exist when you receive the ``query_dict``, so
        you're supposed to test for its existence before, for example, adding a
        new column to the ``select`` key.

        The ``where`` key is a special case. It's elements are on the form:

            (format_string, param1, param2, ...)

        The ``format_string`` isn't escaped for SQL Injection attacks, so
        everything coming from the user should be in the params list. With this
        format, you could do something like:

            ('"age" BETWEEN %s AND %s', age_between[0], age_between[1])

        This escapes the ``age_between[0]`` and ``age_between[1]`` making sure
        we're not vulnerable.

        After finishing this, you should return your modified ``query_dict``.

        :param context: the context
        :type context: dictionary
        :param data_dict: the parameters received from the user
        :type data_dict: dictionary
        :param fields_types: the current resource's fields as dict keys and
            their types as values
        :type fields_types: dictionary
        :param query_dict: the current query_dict, as changed by the IDatastore
            extensions that ran before yours
        :type query_dict: dictionary

        :returns: the query_dict with your modifications
        :rtype: dictionary
        '''
        print 'WE ARE GERE'
        print query_dict
        return query_dict

class INHSDatastoreBackend(interfaces.Interface):
    """Allow custom implementations of datastore backend"""
    def register_backends(self):
        """
        Register classes that inherits from DatastoreBackend.

        Every registered class provides implementations of DatastoreBackend
        and, depending on `datastore.write_url`, one of them will be used
        inside actions.

        `ckanext.datastore.DatastoreBackend` has method `set_active_backend`
        which will define most suitable backend depending on schema of
        `ckan.datastore.write_url` config directive. eg. 'postgresql://a:b@x'
        will use 'postgresql' backend, but 'mongodb://a:b@c' will try to use
        'mongodb' backend(if such backend has been registered, of course).
        If read and write urls use different engines, `set_active_backend`
        will raise assertion error.


        :returns: the dictonary with backend name as key and backend class as
                  value
        """
        print 'HERE nhs'
        print 'HERE nhs'
        return {}