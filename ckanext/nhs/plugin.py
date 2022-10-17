from flask import Blueprint
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from routes.mapper import SubMapper
from ckanext.nhs import helpers
from ckan.lib.plugins import DefaultTranslation
from ckanext.nhs.controller import (
    followed_datasets, followed_organizations, SelfDelete,
    ReportDataset
)
from flask import  copy_current_request_context

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
            'get_dataset_report_type' : helpers.get_dataset_report_type,
        }

    # IRoutes
    def before_map(self, map):
        nhs_controller = 'ckanext.nhs.controller:NHSController'
        with SubMapper(map, controller=nhs_controller) as m:
            m.connect('copy_data_dict', '/dataset/{id}/dictionary/{target}/copy', action='copy_data_dict')
            m.connect('/organization/{url:.*}', action='org_redirect')

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
        blueprint.add_url_rule('/user/me/delete/<id>', 
            view_func=SelfDelete.as_view('self_delete'))
        blueprint.add_url_rule('/dataset/<id>/report', 
            view_func=ReportDataset.as_view('report_dataset'))

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


import ckan.model as model
import ckan.logic as logic
import datetime
from ckan.common import ungettext, config
import ckan.lib.base as base

def _notifications_for_nhs_activities(activities, new_package_activity, new_resource_activity, user_dict):
    '''Return one or more email notifications covering the given activities.
    This function handles grouping multiple activities into a single digest
    email.
    :param activities: the activities to consider
    :type activities: list of activity dicts like those returned by
        ckan.logic.action.get.dashboard_activity_list()
    :returns: a list of email notifications
    :rtype: list of dicts each with keys 'subject' and 'body'
    '''
    if not (new_package_activity or new_resource_activity):
        return []

    if not user_dict.get('activity_streams_email_notifications'):
        return []

    # We just group all activities into a single "new activity" email that
    # doesn't say anything about _what_ new activities they are.
    # TODO: Here we could generate some smarter content for the emails e.g.
    # say something about the contents of the activities, or single out
    # certain types of activity to be sent in their own individual emails,
    # etc.

    subject = "New data added to NHSBSA Open Data Portal"
        
    body = base.render(
            'activity_streams/activity_stream_email_resource_notifications.html',
            extra_vars={'pkg_activities': new_package_activity, 
            'resource_activities': new_resource_activity})
    
    notifications = [{
        'subject': subject,
        'body': body
        }]

    return notifications        

def _notifications_from_nhs_dashboard_activity_list(user_dict, since):
    '''Return any email notifications from the given user's dashboard activity
    list since `since`.
    '''
    # Get the user's dashboard activity stream.
    context = {'model': model, 'session': model.Session,
            'user': user_dict['id']}
    activity_list = logic.get_action('dashboard_activity_list')(context, {})
    # Filter out the user's own activities., so they don't get an email every
    # time they themselves do something (we are not Trac).
    activity_list = [activity for activity in activity_list
            if activity['user_id'] != user_dict['id']]
    # Filter out the old activities.
    strptime = datetime.datetime.strptime
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    activity_list = [activity for activity in activity_list
            if strptime(activity['timestamp'], fmt) > since]

    activity_detail = []
    new_resource_activity = []
    new_package_activity = []
    for activity in activity_list:
        activity_detail = logic.get_action('activity_detail_list')(context, {'id': activity['id']})
        for act_det in activity_detail:
            if act_det['activity_type'] == 'new':
                if act_det['object_type'] == 'Package': 
                    new_package_activity.append(act_det)
                if act_det['object_type'] == 'Resource':
                    pkg_name = logic.get_action('package_show')(context, {'id': act_det['data']['resource']['package_id']})['name']
                    act_det['data']['resource']['pkg_name'] = pkg_name
                    new_resource_activity.append(act_det)

    return _notifications_for_nhs_activities(activity_list, new_package_activity, new_resource_activity, user_dict)
