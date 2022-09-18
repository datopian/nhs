from flask import Blueprint
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from routes.mapper import SubMapper
from ckanext.nhs import helpers
from ckan.lib.plugins import DefaultTranslation
from ckanext.nhs.controller import followed_datasets, followed_organizations

from ckanext.datastore.backend import (
    DatastoreException,
    _parse_sort_clause,
    DatastoreBackend
)
from ckanext.nhs.backend.postgres import NHSDatastorePostgresqlBackend


class NHSPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IBlueprint)


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
            'get_resource_data_dictionary': helpers.get_resource_data_dictionary,
            'get_latest_themes': helpers.get_latest_themes,
            'get_themes': helpers.get_themes,
            'get_latest_datasets': helpers.get_latest_datasets,
            'get_latest_resources': helpers.get_latest_resources,
            'get_cookie_control_config': helpers.get_cookie_control_config,
            'get_googleanalytics_config': helpers.get_googleanalytics_config,
            'resource_view_get_fields' : helpers.resource_view_get_fields,
            'resource_convert_schema' : helpers.resource_convert_schema,
        }

    # IRoutes
    def before_map(self, map):
        nhs_controller = 'ckanext.nhs.controller:NHSController'
        with SubMapper(map, controller=nhs_controller) as m:
            m.connect('copy_data_dict', '/dataset/{id}/dictionary/{target}/copy', action='copy_data_dict')
            m.connect('/organization/{url:.*}', action='org_redirect')

        map.redirect('/about', '/pages/about',
                    _redirect_code='301 Moved Permanently')

        map.redirect('/group', '/',
                     _redirect_code='301 Moved Permanently')
        map.redirect('/group/{url}?{qq}', '/',
                     _redirect_code='301 Moved Permanently')
        map.redirect('/dataset/groups/{url}?{qq}', '/dataset/{url}{query}',
                     _redirect_code='301 Moved Permanently')

        map.redirect('/organization', '/theme',
                     _redirect_code='301 Moved Permanently')
        map.redirect('/organization/', '/theme',
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
                          'members',
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

    # IBlueprint
    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''
        # Create Blueprint for plugin
        blueprint = Blueprint(u'nhs', __name__)
        blueprint.template_folder = u'templates'
        # Add plugin url rules to Blueprint object
        blueprint.add_url_rule('/dashboard/followed/datasets', 
            view_func=followed_datasets)
        blueprint.add_url_rule('/dashboard/followed/organizations', 
            view_func=followed_organizations)

        return blueprint

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


class NHSDatastorePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IDomainObjectModification)

    # IDatastoreBackend

    def register_backends(self):
        return {
            'postgresql': NHSDatastorePostgresqlBackend,
            'postgres': NHSDatastorePostgresqlBackend,
        }

    # IConfigurer

    def update_config(self, config_):
        NHSDatastorePostgresqlBackend.register_backends()
        NHSDatastorePostgresqlBackend.set_active_backend(config_)

        templates_base = config_.get('ckan.base_templates_folder')

        toolkit.add_template_directory(config_, templates_base)
        self.backend = NHSDatastorePostgresqlBackend.get_active_backend()


    def configure(self, config_):
        self.config = config_
        self.backend.configure(config_)