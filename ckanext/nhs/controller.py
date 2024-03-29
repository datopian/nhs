import logging
import requests
from six import string_types
from urllib import urlencode
from flask.views import MethodView
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.activity_streams as activity_streams

from ckan.controllers.package import PackageController

from ckan.lib.base import BaseController, render
from ckan.plugins.toolkit import (
    ObjectNotFound, NotAuthorized, get_action, get_validator, _, request,
    abort, render, c, h, check_access
)
from ckan.common import request
from ckan.controllers.organization import OrganizationController
from ckan.controllers.user import UserController

import ckan.lib.plugins
import ckan.model as model
import ckan.lib.search as search
from ckan.common import OrderedDict, config
import ckan.lib.helpers as core_helpers
from ckanext.nhs.mailer import mail_dataset_report
lookup_group_controller = ckan.lib.plugins.lookup_group_controller

log = logging.getLogger(__name__)

class NHSController(BaseController):
    def _prepare(self, id, resource_id):
        try:
            pkg_dict = get_action(u'package_show')(None, {u'id': id})
            resource = get_action(u'resource_show')(None, {u'id': resource_id})
            rec = get_action(u'datastore_search')(
                None, {
                    u'resource_id': resource_id,
                    u'limit': 0
                }
            )
            return {
                u'pkg_dict': pkg_dict,
                u'resource': resource,
                u'fields': [
                    f for f in rec[u'fields'] if not f[u'id'].startswith(u'_')
                ]
            }

        except (ObjectNotFound, NotAuthorized):
            abort(400, _(u'Cannot Copy from this resource. Please choose correct resource.'))

    def copy_data_dict(self, id, target):
        '''
            Method to copy the data dictonary from source to target.
            @params: - copy_data_dict - Fetched from select in HTML
            @return - rendered HTML of Data Dictionary
        '''
        data_dict = self._prepare(id, target)
        if request.params.get('copy_data_dict'):
            source = request.params.get('copy_data_dict')
            source_data_dict = self._prepare(id, source)
            data_dict['fields'] = source_data_dict['fields']
        c.pkg_dict = data_dict[u'pkg_dict']
        c.resource = data_dict[u'resource']
        return render(u'datastore/dictionary.html', data_dict)

    def org_redirect(self, url):
        req_query = request.query_string
        return core_helpers.redirect_to('/theme/{url}?{req_query}'
            .format(url=url, req_query=req_query))

  
class NhsOrganizationController(OrganizationController):
    def _guess_group_type(self, expecting_name=False):
        """
            The base CKAN function gets the group_type from the URL,
            this is a problem in the case when the URL mapping is changed
            and instead of group we use something else.
            That will require overriding the OrganizationController.

        """
        gt = 'organization'

        return gt

    def _read(self, id, limit, group_type):
        ''' This is common code used by both read and bulk_process'''
        context = {'model': model, 'session': model.Session,
                   'user': c.user,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True, 'extras_as_string': True}

        q = c.q = request.params.get('q', '')
        # Search within group
        if c.group_dict.get('is_organization'):
            fq = 'owner_org:"%s"' % c.group_dict.get('id')
        else:
            fq = 'groups:"%s"' % c.group_dict.get('name')

        c.description_formatted = \
            h.render_markdown(c.group_dict.get('description'))

        context['return_query'] = True

        page = h.get_page_number(request.params)

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']
        sort_by = request.params.get('sort', None)

        def search_url(params):
            controller = lookup_group_controller(group_type)
            action = 'bulk_process' if c.action == 'bulk_process' else 'read'
            url = h.url_for(controller=controller, action=action, id=id)
            params = [(k, v.encode('utf-8') if isinstance(v, string_types)
                       else str(v)) for k, v in params]
            return url + u'?' + urlencode(params)

        def drill_down_url(**by):
            return h.add_url_param(alternative_url=None,
                                   controller='group', action='read',
                                   extras=dict(id=c.group_dict.get('name')),
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            controller = lookup_group_controller(group_type)
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller=controller, action='read',
                                      extras=dict(id=c.group_dict.get('name')))

        c.remove_field = remove_field

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

        try:
            c.fields = []
            c.fields_grouped = {}
            search_extras = {}
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        q += ' %s: "%s"' % (param, value)
                        if param not in c.fields_grouped:
                            c.fields_grouped[param] = [value]
                        else:
                            c.fields_grouped[param].append(value)
                    else:
                        search_extras[param] = value

            facets = OrderedDict()

            default_facet_titles = {'organization': _('Organizations'),
                                    'groups': _('Groups'),
                                    'tags': _('Tags'),
                                    'res_format': _('Formats'),
                                    'license_id': _('Licenses')}

            for facet in h.facets():
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            self._update_facet_titles(facets, group_type)

            c.facet_titles = facets

            data_dict = {
                'q': q,
                'fq': fq,
                'include_private': True,
                'include_drafts': True,
                'facet.field': facets.keys(),
                'rows': limit,
                'sort': sort_by,
                'start': (page - 1) * limit,
                'extras': search_extras
            }

            context_ = dict((k, v) for (k, v) in context.items()
                            if k != 'schema')
            query = get_action('package_search')(context_, data_dict)

            c.page = core_helpers.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )

            c.group_dict['package_count'] = query['count']

            c.search_facets = query['search_facets']
            c.search_facets_limits = {}
            for facet in c.search_facets.keys():
                limit = int(request.params.get('_%s_limit' % facet,
                            config.get('search.facets.default', 10)))
                c.search_facets_limits[facet] = limit
            c.page.items = query['results']

            c.sort_by_selected = sort_by

        except search.SearchError as se:
            log.error('Group search error: %r', se.args)
            c.query_error = True
            c.page = h.Page(collection=[])

        self._setup_template_variables(context, {'id': id},
                                       group_type=group_type)

class NhsUserController(UserController):

    def register(self, data=None, errors=None, error_summary=None):
        return abort(403, _('Unauthorized to register a user.'))


def _datasets_or_groups_followed_by_user(type):
    """Return a list of dataset/groups/organization followed by the user."""
    context = {'for_view': True, 'user': c.user,
                'auth_user_obj': c.userobj}
    data_dict = {'user_obj': c.userobj, 'include_datasets': False}
    c.is_sysadmin = ckan.authz.is_sysadmin(c.user)
    try:
        user_dict = get_action('user_show')(context, data_dict)
        if type == 'dataset':
            user_dict['datasets']  = get_action('dataset_followee_list')(context, {
                    'id': user_dict['id'],
                })
        elif type =='organization':
            user_dict['organizations'] = get_action('organization_followee_list')(context, {
                'id': user_dict['id']
            })
        elif type =='group':
            user_dict['groups'] = get_action('group_followee_list')(context, {
                'id': user_dict['id']
            })

    except ObjectNotFound:
        h.flash_error(_('Not authorized to see this page'))
        h.redirect_to(controller='user', action='login')
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))

    c.user_dict = user_dict
    c.is_myself = user_dict['name'] == c.user
    c.about_formatted = h.render_markdown(user_dict['about'])


def followed_datasets():
    _datasets_or_groups_followed_by_user('dataset')
    return render('user/followed_datasets.html', extra_vars={'user_dict':c.user_dict}) 

def followed_organizations():
    _datasets_or_groups_followed_by_user('organization')
    return render('user/followed_organizations.html', extra_vars={'user_dict':c.user_dict})

def _reCapatcha_verify(response_token):
        secret_key = config.get('ckanext.nhs.recaptcha_secret_key')
        
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
            'secret': secret_key,
            'response': response_token
        })

        return response.json()



class SelfDelete(MethodView):
    '''Delete self account'''

    def post(self, id):
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user,
            'auth_user_obj': c.userobj
            }

        data_dict = {'id': id}

        def _get_repoze_handler(handler_name):
            return getattr(request.environ[u'repoze.who.plugins'][u'friendlyform'],
                        handler_name)
        try:
            check_access('user_update', context, {'id': id})
            context['ignore_auth'] = True
            get_action(u'user_delete')(context, data_dict)
            
            # Delete user permanently from the database table
            user = model.User.get(id)
            model.Session.delete(user)
            model.Session.commit()

            try:
                # Delete the sso user token from the database
                from ckanext.oauth2.db import UserToken
                user = UserToken.by_user_name(user.name)
                model.Session.delete(user)
                model.Session.commit()
            except:
                pass

            url = h.url_for(u'home.index')
            h.flash_success(_(u'You\'ve successfully deleted your account.'))
            return h.redirect_to(
                _get_repoze_handler(u'logout_handler_path') + u'?came_from=' + url,
                parse_url=True)
        except NotAuthorized:
            msg = _(u'Unauthorized to delete user with id "{user_id}".')
            abort(403, msg.format(user_id=id))


class ReportDataset(MethodView):
    def post(self, id):
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user,
            'auth_user_obj': c.userobj
            }
        data_dict = {'id': id}

        recaptcha = request.form.get('g-recaptcha-token')
        
        try:
            captcha_result = _reCapatcha_verify(recaptcha)
            log.info('Captcha Result: {0}'.format(captcha_result))
            if captcha_result['success'] == False:
                raise Exception
        except Exception as e:
            h.flash_error(_('Unable to report dataset, Please verify that you are not a robot.'))
            return h.redirect_to(controller='package', action='read', id=data_dict['id'])

        report_dict = {
            'issue_type' : request.form.get('type'),
            'issue_description' : request.form.get('description'),
            'email' : request.form.get('email', False)
        }

        try:
            mail_dataset_report(data_dict['id'], report_dict)
            h.flash_success(_('Thank you for reporting your issue. We will review and respond shortly'))
            return h.redirect_to(controller='package', action='read', id=data_dict['id'])
        except Exception as e :
            msg = _(u'Unable to report dataset with id "{dataset_id}". Please contact administrator for more information.')
            abort(502, msg.format(dataset_id=data_dict['id']))




class FOIPackageController(PackageController):
    """
        FOI Package controller
    """
    def __init__(self):
        super(FOIPackageController, self).__init__()

    def _guess_package_type(self, expecting_name=False):
        """
            Guess the type of package from the URL handling the case
            where there is a prefix on the URL (such as /data/package)
        """
        # Special case: if the rot URL '/' has been redirected to the package
        # controller (e.g. by an IRoutes extension) then there's nothing to do
        # here.
        if request.path == '/':
            return 'dataset'

        parts = [x for x in request.path.split('/') if x]

        idx = -1
        if expecting_name:
            idx = -2

        package_type = parts[idx]
        if package_type == 'package' or 'foi-responses':
            package_type = 'dataset'

        return package_type
    
class ManagementController(MethodView):
    def _prepare(self):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': c.user,
            u'auth_user_obj': c.userobj,
        }
        try:
            check_access(u'sysadmin', context)
        except NotAuthorized:
            abort(403, _(u'Unauthorized to view management page'))
        return context
     
    def get(self):
        activities = get_action(u'issue_comment_activity_list_html')(self._prepare(), { u'limit': 0})
        query = model.Session.query(
            model.User
        ).filter(model.User.state == u'active') \
        .filter(model.User.name != u'default') \
        .order_by(model.User.name)

        users_list = [model_dictize.user_dictize(user, self._prepare()) for user in query.all()]
        
        return render(u'admin/management.html', extra_vars={
            'user_dict': {},
            'activities': activities,
            'default_limit': 5,
            'users_list': users_list,
            })
