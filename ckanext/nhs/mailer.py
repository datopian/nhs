from ckan.lib.mailer import mail_user
from ckan import model
from ckan.lib.base import render_jinja2
import ckan.plugins.toolkit as tk


def mail_dataset_report(dataset_id, report_dict):
    sysadmins = model.Session.query(model.User).filter(
        model.User.state != model.State.DELETED,
        model.User.sysadmin == True
        ).all()

    email_subject = "New dataset report"

    context = {'model': model, 'session': model.Session, 'ignore_auth': True}

    dataset_dict = tk.get_action('package_show')(context, {'id': dataset_id})

    for sysadmin in sysadmins:
        email_body = _dataset_report_email_body(sysadmin, report_dict, dataset_dict)
        if sysadmin.email:
            mail_user(sysadmin, email_subject, email_body)


def _dataset_report_email_body(user, report_dict, dataset_dict):
    extra_vars = {
        'site_title': tk.config.get('ckan.site_title'),
        'site_url': tk.config.get('ckan.site_url'),
        'user_name': user.name,
        'dataset_dict': dataset_dict,
        'topic': report_dict.get('topic', ''),
        'description': report_dict.get('description', '')
        }
    return render_jinja2('emails/report_dataset.txt', extra_vars)

