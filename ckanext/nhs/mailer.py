from ckan.lib.mailer import mail_recipient
from ckan import model
from ckan.lib.base import render_jinja2
import ckan.plugins.toolkit as tk

from ckanext.nhs.lib import mail_html

def mail_dataset_report(dataset_id, report_dict):
    email_to = tk.config.get('ckanext.nhs.dataset_report_email_to', False)

    email_subject = "A new issue has been reported on the Open Data Portal"

    context = {'model': model, 'session': model.Session, 'ignore_auth': True}

    dataset_dict = tk.get_action('package_show')(context, {'id': dataset_id})

    if email_to:
        email_body = _dataset_report_email_body(report_dict, dataset_dict)
        try:
            site_title = tk.config.get('ckan.site_title')
            site_url = tk.config.get('ckan.site_url')
            return mail_html('', email_to,
                                site_title, site_url, email_subject, email_body,
                                headers={})
        except Exception as e:  
            print(e)

def _dataset_report_email_body(report_dict, dataset_dict):
    extra_vars = {
        'site_title': tk.config.get('ckan.site_title'),
        'site_url': tk.config.get('ckan.site_url'),
        'dataset_title': dataset_dict['title'],
        'dataset_url': tk.h.url_for(controller='package', action='read', id=dataset_dict['name']),
        'issue_type': report_dict.get('issue_type', ''),
        'issue_description': report_dict.get('issue_description', ''),
        'email':  report_dict.get('email', ''),
        }
    return render_jinja2('emails/report_dataset.html', extra_vars)

