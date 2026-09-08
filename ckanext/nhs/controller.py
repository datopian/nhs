import logging
import requests
import csv
import io
from flask.views import MethodView
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
from sqlalchemy import or_, text

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
from flask import redirect, Response
from ckanext.activity.model import Activity
from ckanext.activity.model.activity import _activities_limit, activity_list_dictize
import ckan.plugins.toolkit as tk
import datetime

log = logging.getLogger(__name__)

# Characters that make a spreadsheet treat a cell as a formula rather than text.
_CSV_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def _csv_safe(value):
    """Stop user-supplied text in an export being evaluated as a formula.

    Excel, LibreOffice and Sheets all evaluate a cell whose value starts with
    '=', '+', '-', '@' or a leading tab/CR. CSV quoting does not prevent this,
    so any user-controlled field written to an export has to be neutralised
    explicitly. Prefixing with an apostrophe marks the cell as literal text.
    """
    if isinstance(value, str) and value[:1] in _CSV_FORMULA_PREFIXES:
        return "'" + value
    return value


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
    log.info('Response token is {}'.format(response_token))
    log.info('Secret key is {}'.format(secret_key))
    
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': secret_key,
        'response': response_token
    })

    log.info('Response is {}'.format(response.json()))

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
            log.info(e)
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
        activity_types_to_filter = [
    u'changed issue',
    u'new issue',
    u'issue closed',
    u'issue reopened',
    u'issue deleted'
]
        limit = int(tk.request.args.get("limit", 5))
        q = model.Session.query(Activity)
        q = q.filter(Activity.activity_type.in_(activity_types_to_filter))
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

class ExtractUsersAPI(MethodView):
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
            abort(403, _('Unauthorized'))
        return context

    def get(self):
        self._prepare()
        
        def iter_csv():
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write Header
            writer.writerow(['Username', 'Full Name', 'Email', 'Registered Date', 'Alert Emails (Y/N)', 'Followed Themes (Orgs)', 'Followed Datasets', 'State'])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            
            session = model.Session
            
            user_query = text("""
                SELECT id, name, fullname, email, created, activity_streams_email_notifications, state 
                FROM "user" 
                WHERE state != 'deleted' 
                ORDER BY created DESC
            """)
            users = session.execute(user_query).fetchall()
            
            for u in users:
                uid, username, fullname, email, created, email_notif, state = u
                
                alert_val = 'Y' if email_notif is None or email_notif else 'N'
                
                g_query = text("""
                    SELECT g.title FROM "group" g 
                    JOIN user_following_group ufg ON g.id = ufg.object_id 
                    WHERE ufg.follower_id = :uid
                """)
                groups_str = ", ".join([g[0] for g in session.execute(g_query, {'uid': uid}).fetchall()])
                
                d_query = text("""
                    SELECT p.title FROM package p 
                    JOIN user_following_dataset ufd ON p.id = ufd.object_id 
                    WHERE ufd.follower_id = :uid
                """)
                datasets_str = ", ".join([d[0] for d in session.execute(d_query, {'uid': uid}).fetchall()])
                
                writer.writerow([
                    _csv_safe(username), _csv_safe(fullname), _csv_safe(email),
                    created, alert_val, _csv_safe(groups_str),
                    _csv_safe(datasets_str), state,
                ])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        return Response(
            iter_csv(), 
            mimetype="text/csv", 
            headers={"Content-Disposition": "attachment; filename=users_extract.csv"}
        )

class ExtractActivityAPI(MethodView):
    # Rows fetched per round-trip while streaming the activity range.
    batch_size = 1000

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
            abort(403, _('Unauthorized'))
        return context

    def get(self):
        context = self._prepare()
        
        # Parse query parameters "since" and "until"
        # Since defaults to start of current month. Until defaults to now.
        since_str = request.args.get('since')
        until_str = request.args.get('until')
        
        now = datetime.datetime.utcnow()
        if until_str:
            try:
                until_dt = datetime.datetime.fromisoformat(until_str)
            except ValueError:
                abort(400, "Invalid 'until' format. Use ISO format YYYY-MM-DD")
        else:
            until_dt = now
            
        if since_str:
            try:
                since_dt = datetime.datetime.fromisoformat(since_str)
            except ValueError:
                abort(400, "Invalid 'since' format. Use ISO format YYYY-MM-DD")
        else:
            # Default: first day of the current month at midnight UTC
            since_dt = until_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # A reversed range matches nothing, which would stream a header-only CSV
        # with a 200 - indistinguishable from a genuine failure. Reject it here.
        if since_dt > until_dt:
            abort(400, "'since' must not be later than 'until'")

        def iter_csv():
            output = io.StringIO()
            writer = csv.writer(output)

            # Write Header
            writer.writerow(['Date of activity', 'Type of activity', 'Dataset', 'Theme', 'Discussion comment'])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            session = model.Session

            # Stream the activities in the date range rather than materialising
            # them, via a server-side cursor (stream_results + max_row_buffer)
            # so memory stays flat regardless of range width.
            #
            # activity.data stores a full JSON snapshot of the affected
            # package/resource/group - for a 'changed package' event on a
            # dataset with many resources this can be several MB, and CKAN's
            # column type fully deserialises it the instant it's read,
            # regardless of how much of it is actually used. Only a handful of
            # short fields are needed per row, so those are extracted directly
            # in SQL instead of pulling the whole blob into Python: the CTE
            # casts data to jsonb exactly once per row (MATERIALIZED - without
            # it Postgres may re-inline the cast per column, re-parsing the
            # same blob once per extracted field), and only the small
            # extracted strings ever cross into the app's memory.
            query = text("""
                WITH parsed AS MATERIALIZED (
                    SELECT "timestamp", activity_type, CAST(data AS JSONB) AS d
                    FROM activity
                    WHERE "timestamp" >= :since_dt AND "timestamp" <= :until_dt
                )
                SELECT
                    "timestamp", activity_type,
                    (d ? 'package')  AS has_package,
                    d->'package'->>'title'  AS pkg_title,
                    d->'package'->>'name'   AS pkg_name,
                    d->'package'->>'owner_org' AS pkg_org,
                    (d ? 'resource') AS has_resource,
                    d->'resource'->>'package_id' AS res_pkgid,
                    d->'resource'->>'name'  AS res_name,
                    (d ? 'group')    AS has_group,
                    d->'group'->>'title'    AS grp_title,
                    d->'group'->>'name'     AS grp_name,
                    d->>'title'   AS issue_title,
                    d->>'comment' AS issue_comment
                FROM parsed
                ORDER BY "timestamp" DESC
            """).execution_options(stream_results=True, max_row_buffer=self.batch_size)
            q = session.execute(query, {"since_dt": since_dt, "until_dt": until_dt})

            # Cache org titles to avoid repeated DB lookups (~20 unique orgs)
            org_cache = {}

            def _cached_org_title(org_id):
                if not org_id:
                    return ''
                if org_id not in org_cache:
                    row = session.execute(
                        text('SELECT title FROM "group" WHERE id = :oid'),
                        {'oid': org_id}
                    ).fetchone()
                    org_cache[org_id] = row[0] if row else ''
                return org_cache[org_id]

            # Resource activities need their parent dataset looked up. Over a wide
            # range the same datasets recur constantly, so cache them the same way.
            pkg_cache = {}

            def _cached_package(package_id):
                if package_id not in pkg_cache:
                    row = session.execute(
                        text('SELECT title, owner_org FROM package WHERE id = :pid'),
                        {'pid': package_id}
                    ).fetchone()
                    pkg_cache[package_id] = (row[0] or '', row[1]) if row else ('', None)
                return pkg_cache[package_id]

            # ckanext-issues stores issue/comment fields at the TOP LEVEL of
            # activity.data (not nested under data['issue'] or data['issue_comment']).
            # See _create_issues_activity in ckanext-issues.
            issue_activity_types = {
                'new issue', 'changed issue', 'issue closed',
                'issue reopened', 'issue deleted', 'issue comment deleted'
            }
            # Remap DB activity types to user-friendly labels
            activity_type_display = {
                'new package': 'new dataset',
                'changed package': 'changed dataset',
                'deleted package': 'deleted dataset',
                'new issue': 'new discussion',
                'changed issue': 'changed discussion',
                'issue closed': 'discussion closed',
                'issue reopened': 'discussion reopened',
                'issue deleted': 'discussion deleted',
                'issue comment deleted': 'discussion comment deleted',
            }

            rows_written = 0
            try:
                for (timestamp, activity_type, has_package, pkg_title, pkg_name,
                     pkg_org, has_resource, res_pkgid, res_name, has_group,
                     grp_title, grp_name, issue_title, issue_comment) in q:
                    date_str = timestamp.isoformat() if timestamp else ''
                    act_type = activity_type or ''
                    dataset_title = ''
                    theme_title = ''
                    discussion_comment = ''

                    # --- Dataset / Theme extraction ---
                    if has_package:
                        dataset_title = pkg_title or pkg_name or ''
                        theme_title = _cached_org_title(pkg_org)

                    elif has_resource:
                        package_id = res_pkgid or ''
                        if package_id:
                            dataset_title, owner_org = _cached_package(package_id)
                            theme_title = _cached_org_title(owner_org)
                        if not dataset_title:
                            dataset_title = res_name or ''

                    elif has_group:
                        theme_title = grp_title or grp_name or ''

                    # --- Discussion comment extraction ---
                    # Issue/comment fields are FLAT at data root, not nested
                    if act_type in issue_activity_types:
                        title_text = issue_title or ''
                        comment_text = issue_comment or ''

                        if title_text and comment_text:
                            discussion_comment = 'Discussion: {} | Comment: {}'.format(title_text, comment_text)
                        elif title_text:
                            discussion_comment = 'Discussion: {}'.format(title_text)
                        elif comment_text:
                            discussion_comment = 'Comment: {}'.format(comment_text)

                    display_type = activity_type_display.get(act_type, act_type)
                    # date_str and display_type are code-generated; the other
                    # three carry user-supplied text and need neutralising.
                    writer.writerow([
                        date_str, display_type, _csv_safe(dataset_title),
                        _csv_safe(theme_title), _csv_safe(discussion_comment),
                    ])
                    rows_written += 1
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)
            except Exception:
                # The header row is already on the wire, so the client cannot be
                # given a proper error status. Log what happened and how far we
                # got, then re-raise: aborting the chunked response makes the
                # download fail visibly instead of looking like an empty CSV.
                log.exception(
                    'Activity extract failed after %s rows for range %s..%s',
                    rows_written, since_dt.isoformat(), until_dt.isoformat()
                )
                raise

            log.info(
                'Activity extract streamed %s rows for range %s..%s',
                rows_written, since_dt.isoformat(), until_dt.isoformat()
            )

        return Response(
            iter_csv(), 
            mimetype="text/csv", 
            headers={"Content-Disposition": "attachment; filename=activity_extract.csv"}
        )
