from flask import Blueprint
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.nhs import helpers
from ckan.lib.plugins import DefaultTranslation
from ckan.views.group import register_group_plugin_rules
from ckanext.nhs.controller import (
    followed_datasets,
    followed_organizations,
    SelfDelete,
    ReportDataset,
    ManagementController,
    copy_data_dict,
    org_redirect
)
from ckanext.nhs import validators
from flask import copy_current_request_context, redirect

from ckanext.datastore.backend import (
    DatastoreException,
    _parse_sort_clause,
    DatastoreBackend,
)
from ckanext.nhs.backend.postgres import NHSDatastorePostgresqlBackend
import ckan.model as model
import ckan.logic as logic
import datetime
from ckan.common import ungettext, config
import ckan.lib.base as base
import logging
log = logging.getLogger(__name__)


class NHSPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IValidators)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "nhs")

    # ITemplateHelpers
    def get_helpers(self):
        """
        Define custom helpers (or override existing ones).
        Available as h.{helper-name}() in templates.
        """
        return {
            "get_resources_list": helpers.get_resources_list,
            "get_resources_list_dropdown": helpers.get_resource_list_dropdown,
            "get_dataset_data_dictionary": helpers.get_dataset_data_dictionary,
            "get_resource_data_dictionary": helpers.get_resource_data_dictionary,
            "get_latest_themes": helpers.get_latest_themes,
            "get_themes": helpers.get_themes,
            "get_latest_datasets": helpers.get_latest_datasets,
            "get_latest_resources": helpers.get_latest_resources,
            "get_random_resource_field": helpers.get_random_resource_field,
            "get_datastore_resource_fields": helpers.get_datastore_resource_fields,
            "get_cookie_control_config": helpers.get_cookie_control_config,
            "get_googleanalytics_config": helpers.get_googleanalytics_config,
            "resource_view_get_fields": helpers.resource_view_get_fields,
            "resource_convert_schema": helpers.resource_convert_schema,
            "get_dataset_report_type": helpers.get_dataset_report_type,
            "API_enabled": helpers.API_enabled,
            "get_foi_org_id": helpers.get_foi_org_id,
            "get_recaptcha_site_key": helpers.get_recaptcha_site_key,
            "get_signed_url": helpers.get_signed_url,
            "get_config_value": helpers.get_config_value,
            "get_resource_row_count": helpers.get_resource_row_count,
            "get_popular_tags": helpers.get_popular_tags,
            "get_issue_comment_activity_list": helpers.get_issue_comment_activity_list,
            "get_organization_id_from_path": helpers.get_organization_id_from_path
        }

    # IRoutes method has been converted to IBlueprint

    # IBlueprint
    def get_blueprint(self):
        """Return a Flask Blueprint object to be registered by the app."""
        # Create Blueprint for plugin
        blueprint = Blueprint("nhs", __name__)
        blueprint.template_folder = "templates"
        # Add plugin url rules to Blueprint object
        blueprint.add_url_rule(
            "/dashboard/followed/datasets", view_func=followed_datasets
        )
        blueprint.add_url_rule(
            "/dashboard/followed/organizations", view_func=followed_organizations
        )
        blueprint.add_url_rule(
            "/user/me/delete/<id>", view_func=SelfDelete.as_view("self_delete")
        )
        blueprint.add_url_rule(
            "/dataset/<id>/report", view_func=ReportDataset.as_view("report_dataset")
        )

        blueprint.add_url_rule(
            "/dashboard/management",
            view_func=ManagementController.as_view("management"),
        )
        
        blueprint.add_url_rule(
            "/dataset/<id>/dictionary/<target>/copy",
            view_func=copy_data_dict
        )
        
        # Add permanent redirects from IRoutes
        @blueprint.route("/group")
        def redirect_group():
            return redirect("/", code=301)
            
        @blueprint.route("/group/<url>")
        def redirect_group_url(url):
            return redirect("/", code=301)
            
        @blueprint.route("/dataset/groups/<url>")
        def redirect_dataset_groups(url):
            query_string = request.query_string.decode("utf-8")
            return redirect(f"/dataset/{url}?{query_string}", code=301)
            
        # Routes for FOI package controller
        blueprint.add_url_rule(
            "/foi-responses",
            endpoint="foi-responses",
            view_func=lambda: redirect("/organization/freedom-of-information-disclosure-log")
        )
                
        # Theme routes (previously using NhsOrganizationController)
        # These routes will now use the core organization controller via redirection to maintain functionality
        # in CKAN 2.11 while keeping the /theme URL structure
        theme = Blueprint(u'theme', __name__, url_prefix=u'/theme',
                  url_defaults={u'group_type': u'organization',
                                u'is_organization': True})
        register_group_plugin_rules(theme)
        return [blueprint, theme]

    # IValidators
    def get_validators(self):
        return {"upload_to_datastore": validators.upload_to_datastore}

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        """
        Override core search fasets for datasets
        """
        from collections import OrderedDict

        facets_dict = OrderedDict({})
        facets_dict["organization"] = "Themes"
        facets_dict["tags"] = "Tags"
        facets_dict["res_format"] = "Formats"
        facets_dict["license_id"] = "Licenses"
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        """
        Override core search fasets for organization
        """
        from collections import OrderedDict

        facets_dict = OrderedDict({})
        facets_dict["organization"] = "Themes"
        facets_dict["tags"] = "Tags"
        facets_dict["res_format"] = "Formats"
        facets_dict["license_id"] = "Licenses"
        return facets_dict

    # IPackageController
    def before_dataset_search(self, search_params):
        if "fq" not in search_params:
            search_params["fq"] = ""

        # Exclude FOI data from default search page
        if toolkit.request.path.startswith("/dataset"):
            foi_filter = "!(organization:freedom-of-information-disclosure-log)"
            if search_params["fq"].strip():  
                search_params["fq"] += " " + foi_filter
            else:
                search_params["fq"] = foi_filter
        
        # show only foi data in a FOI seprate page
        # currently this route does not exist
        # moved to organization/freedom-of-information-disclosure-log

        # elif toolkit.request.path.startswith("/foi-responses"):
        #     search_params[
        #         "fq"
        #     ] += " (organization:freedom-of-information-disclosure-log)"
        # log.info(f"result key is {search_params['fq']}")
        
        return search_params

    def before_show(self, resource):
        if resource and resource.get("zip_url") and resource.get("zip_url") != "None":
            zip_url = resource.get("zip_url")
            url_parts = zip_url.split(".zip", 1)
            if len(url_parts) == 1:
                url_parts = zip_url.split(".ZIP", 1)
            url_before_zip = url_parts[0] + (
                ".zip" if ".zip" in zip_url else (".ZIP" if ".ZIP" in zip_url else "")
            )
            resource["zip_url"] = helpers.get_signed_url(url_before_zip)
        return resource


#class NHSDatastorePlugin(plugins.SingletonPlugin):
#    plugins.implements(plugins.IConfigurer)
#    plugins.implements(plugins.IConfigurable)
#    plugins.implements(plugins.IDomainObjectModification)
#    plugins.implements(plugins.IDatastoreBackend)
#
#    # IDatastoreBackend
#
#    def register_backends(self):
#        return {
#            "postgresql": NHSDatastorePostgresqlBackend,
#            "postgres": NHSDatastorePostgresqlBackend,
#        }
#
#    # IConfigurer
#
#    def update_config(self, config_):
#        NHSDatastorePostgresqlBackend.register_backends()
#        NHSDatastorePostgresqlBackend.set_active_backend(config_)
#
#        templates_base = config_.get("ckan.base_templates_folder")
#
#        toolkit.add_template_directory(config_, templates_base)
#        self.backend = NHSDatastorePostgresqlBackend.get_active_backend()
#
#    def configure(self, config_):
#        self.config = config_
#        self.backend.configure(config_)

def _notifications_for_nhs_activities(
    activities, new_package_activity, new_resource_activity, user_dict
):
    """Return one or more email notifications covering the given activities.
    This function handles grouping multiple activities into a single digest
    email.
    :param activities: the activities to consider
    :type activities: list of activity dicts like those returned by
        ckan.logic.action.get.dashboard_activity_list()
    :returns: a list of email notifications
    :rtype: list of dicts each with keys 'subject' and 'body'
    """
    if not (new_package_activity or new_resource_activity):
        return []

    if not user_dict.get("activity_streams_email_notifications"):
        return []

    # We just group all activities into a single "new activity" email that
    # doesn't say anything about _what_ new activities they are.
    # TODO: Here we could generate some smarter content for the emails e.g.
    # say something about the contents of the activities, or single out
    # certain types of activity to be sent in their own individual emails,
    # etc.

    subject = "New data added to NHSBSA Open Data Portal"

    body = base.render(
        "activity_streams/activity_stream_email_resource_notifications.html",
        extra_vars={
            "pkg_activities": new_package_activity,
            "resource_activities": new_resource_activity,
        },
    )

    notifications = [{"subject": subject, "body": body}]

    return notifications


def _notifications_from_nhs_dashboard_activity_list(user_dict, since):
    """Return any email notifications from the given user's dashboard activity
    list since `since`.
    """
    # Get the user's dashboard activity stream.
    context = {"model": model, "session": model.Session, "user": user_dict["id"]}
    activity_list = logic.get_action("dashboard_activity_list")(context, {})
    # Filter out the user's own activities., so they don't get an email every
    # time they themselves do something (we are not Trac).
    activity_list = [
        activity for activity in activity_list if activity["user_id"] != user_dict["id"]
    ]
    # Filter out the old activities.
    strptime = datetime.datetime.strptime
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    activity_list = [
        activity
        for activity in activity_list
        if strptime(activity["timestamp"], fmt) > since
    ]

    activity_detail = []
    new_resource_activity = []
    new_package_activity = []
    for activity in activity_list:
        activity_detail = logic.get_action("activity_detail_list")(
            context, {"id": activity["id"]}
        )
        for act_det in activity_detail:
            if act_det["activity_type"] == "new":
                if act_det["object_type"] == "Package":
                    new_package_activity.append(act_det)
                if act_det["object_type"] == "Resource":
                    pkg_name = logic.get_action("package_show")(
                        context, {"id": act_det["data"]["resource"]["package_id"]}
                    )["name"]
                    act_det["data"]["resource"]["pkg_name"] = pkg_name
                    new_resource_activity.append(act_det)

    return _notifications_for_nhs_activities(
        activity_list, new_package_activity, new_resource_activity, user_dict
    )
