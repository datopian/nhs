import ckan.logic as logic
import ckan.model as model
from ckan.common import config, is_flask_request, c, request
from ckan.plugins import toolkit


def _get_action(action, context_dict, data_dict):
    return toolkit.get_action(action)(context_dict, data_dict)


def get_resources_list(dataset_id):
    context = {}
    pkg = _get_action('package_search', context, {'q': '', 'fq': 'id:%s' % dataset_id})

    resources = pkg['results'][0]['resources']
    sorted_resources = sorted(resources, key=lambda x: x['created'], reverse=True)

    return sorted_resources


def get_resource_list_dropdown(dataset_id):

    resources = get_resources_list(dataset_id)

    return [{'name': x['id'], 'value': x['name']} for x in resources]
