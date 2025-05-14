import logging
import requests
from flask.views import MethodView
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize

from ckan.lib.base import render
from ckan.plugins.toolkit import (
    ObjectNotFound, NotAuthorized, get_action, _, request,
    abort, render, c, h, check_access
)
from ckan.common import request
import ckan.lib.plugins
import ckan.model as model
from ckan.common import config
from ckanext.nhs.mailer import mail_dataset_report
from flask import redirect
from ckanext.activity.model import Activity
from ckanext.activity.model.activity import _activities_limit, activity_list_dictize
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

def _prepare(id, resource_id):
    try:
        pkg_dict = get_action('package_show')(None, {'id': id})
        resource = get_action('resource_show')(None, {'id': resource_id})
        rec = get_action('datastore_search')(
            None, {
                'resource_id': resource_id,
                'limit': 0
            }
        )
        return {
            'pkg_dict': pkg_dict,
            'resource': resource,
            'fields': [
                f for f in rec['fields'] if not f['id'].startswith('_')
            ]
        }

    except (ObjectNotFound, NotAuthorized):
        abort(400, _('Cannot Copy from this resource. Please choose correct resource.'))

def copy_data_dict(id, target):
    '''
        Method to copy the data dictonary from source to target.
        @params: - copy_data_dict - Fetched from select in HTML
        @return - rendered HTML of Data Dictionary
    '''
    data_dict = _prepare(id, target)
    if request.args.get('copy_data_dict'):
        source = request.args.get('copy_data_dict')
        source_data_dict = _prepare(id, source)
        data_dict['fields'] = source_data_dict['fields']
    return render('datastore/dictionary.html', data_dict)

def org_redirect(url):
    req_query = request.query_string.decode('utf-8')
    redirect_url = '/theme/{url}?{req_query}'.format(
        url=url, req_query=req_query)
    return redirect(redirect_url)


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
    log.info('Secret key is {}'.format(secret_key))
    
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

        try:
            check_access('user_update', context, {'id': id})
            context['ignore_auth'] = True
            get_action('user_delete')(context, data_dict)
            
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

            url = h.url_for('home.index')
            h.flash_success(_('You\'ve successfully deleted your account.'))
            # Flask doesn't use repoze.who, so we just redirect to logout
            return h.redirect_to(h.url_for('user.logout'))
        except NotAuthorized:
            msg = _('Unauthorized to delete user with id "{user_id}".')
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
            return h.redirect_to(h.url_for('dataset.read', id=data_dict['id']))

        report_dict = {
            'issue_type' : request.form.get('type'),
            'issue_description' : request.form.get('description'),
            'email' : request.form.get('email', False)
        }

        try:
            mail_dataset_report(data_dict['id'], report_dict)
            h.flash_success(_('Thank you for reporting your issue. We will review and respond shortly'))
            return h.redirect_to(h.url_for('dataset.read', id=data_dict['id']))
        except Exception as e :
            msg = _('Unable to report dataset with id "{dataset_id}". Please contact administrator for more information.')
            abort(502, msg.format(dataset_id=data_dict['id']))


class ManagementController(MethodView):
    def _prepare(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user,
            'auth_user_obj': c.userobj,
        }
        try:
            check_access('sysadmin', context)
        except NotAuthorized:
            abort(403, _('Unauthorized to view management page'))
        return context
     
    def get(self):
        context = {
        "for_view": True,
        "auth_user_obj": tk.g.userobj,
        }
        limit = int(tk.request.args.get("limit", 5))
        q = model.Session.query(Activity)
        q = q.filter(Activity.activity_type == u'changed issue')
        _activity_objects = _activities_limit(q, limit, 0)
        activities = activity_list_dictize(_activity_objects, context)
        query = model.Session.query(
            model.User
        ).filter(model.User.state == 'active') \
        .filter(model.User.name != 'default') \
        .order_by(model.User.name)

        users_list = [model_dictize.user_dictize(user, self._prepare()) for user in query.all()]
        
        return render('admin/management.html', extra_vars={
            'user_dict': {},
            'activities': activities,
            'limit': limit,
            'load_more_url': h.url_for('nhs.management', limit=limit),
            'default_limit': 5,
            'users_list': users_list,
            })
