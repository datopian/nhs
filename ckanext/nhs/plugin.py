import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from routes.mapper import SubMapper
from ckanext.nhs import helpers
from ckan.lib.plugins import DefaultTranslation


class NHSPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)


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
            'get_dataset_data_dictionary': helpers.get_dataset_data_dictionary,
            'get_latest_themes': helpers.get_latest_themes,
            'get_latest_datasets': helpers.get_latest_datasets,
            'get_latest_resources': helpers.get_latest_resources,
        }

    # IRoutes
    def before_map(self, map):
        nhs_controller = 'ckanext.nhs.controller:NHSController'
        with SubMapper(map, controller=nhs_controller) as m:
            m.connect('copy_data_dict', '/dataset/{id}/dictionary/{target}/copy', action='copy_data_dict')

        map.redirect('/group', '/',
                     _redirect_code='301 Moved Permanently')
        map.redirect('/group/{url}?{qq}', '/',
                     _redirect_code='301 Moved Permanently')
        map.redirect('/dataset/groups/{url}?{qq}', '/dataset/{url}{query}',
                     _redirect_code='301 Moved Permanently')

        map.redirect('/organization', '/theme',
                     _redirect_code='301 Moved Permanently')
        map.redirect('/organization/{url}?{qq}', '/theme/{url}{query}',
                     _redirect_code='301 Moved Permanently')
        org_controller = 'ckanext.nhs.controller:NhsOrganizationController'

        with SubMapper(map, controller=org_controller) as m:
            m.connect('theme_index', '/theme', action='index')
            m.connect('/theme/list', action='list')
            m.connect('/theme_new', action='new')
            m.connect('/theme/new', action='new')
            m.connect('/theme/{action}/{id}',
                      requirements=dict(action='|'.join([
                          'delete',
                          'admins',
                          'member_new',
                          'member_delete',
                          'history'
                          'followers',
                          'follow',
                          'unfollow',
                      ])))
            m.connect('theme_activity', '/theme/activity/{id}',
                      action='activity', ckan_icon='time')
            m.connect('theme_read', '/theme/{id}', action='read')
            m.connect('theme_about', '/theme/about/{id}',
                      action='about', ckan_icon='info-sign')
            m.connect('theme_read', '/theme/{id}', action='read',
                      ckan_icon='sitemap')
            m.connect('theme_edit', '/theme/edit/{id}',
                      action='edit', ckan_icon='edit')
            m.connect('theme_members', '/theme/edit_members/{id}',
                      action='members', ckan_icon='group')
            m.connect('theme_bulk_process',
                      '/theme/bulk_process/{id}',
                      action='bulk_process', ckan_icon='sitemap')
        return map

    def after_map(self, map):
        return map


    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        '''
        Override core search fasets for datasets
        '''
        from collections import OrderedDict
        facets_dict = OrderedDict({})
        facets_dict['organization'] = "Themes"
        facets_dict['tags'] = "Tags"
        facets_dict['res_format'] = "Formats"
        facets_dict['license_id'] = "Licenses"
        return facets_dict


    def organization_facets(self, facets_dict, organization_type, package_type):
        '''
        Override core search fasets for organization
        '''
        from collections import OrderedDict
        facets_dict = OrderedDict({})
        facets_dict['organization'] = "Themes"
        facets_dict['tags'] = "Tags"
        facets_dict['res_format'] = "Formats"
        facets_dict['license_id'] = "Licenses"
        return facets_dict
