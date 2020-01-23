import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.nhs import helpers
from ckanext.nhs.datastore.backend import NHSBackend
from ckanext.datastore.interfaces import IDatastoreBackend


class NHSPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(IDatastoreBackend)

    # IDatastoreBackend
    def register_backends(self):
        return {
            'NHSBackend': NHSBackend,
        }

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'nhs')


    # ITemplateHelpers
    def get_helpers(self):
        '''
        Define custom helpers (or override existing ones).
        Available as h.{helper-name}() in templates.
        '''
        return {
            'get_resources_list': helpers.get_resources_list,
            'get_resources_list_dropdown': helpers.get_resource_list_dropdown,
        }

