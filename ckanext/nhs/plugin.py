import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from routes.mapper import SubMapper
from ckanext.nhs import helpers


class NHSPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)


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
            'get_dataset_data_dictionary': helpers.get_dataset_data_dictionary
        }

    # # IRoutes
    def before_map(self, map):
        nhs_controller = 'ckanext.nhs.controller:NHSController'
        with SubMapper(map, controller=nhs_controller) as m:
            m.connect('copy_data_dict', '/dataset/{id}/dictionary/{target}/copy', action='copy_data_dict')
        return map

    def after_map(self, map):
        return map
