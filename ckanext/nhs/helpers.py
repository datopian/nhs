import ckan.logic as logic
import ckan.model as model
from ckan.common import config, is_flask_request, c, request
from ckan.plugins import toolkit
from ckan.lib.dictization import table_dictize
import ckan.lib.dictization.model_dictize as model_dictize
from sqlalchemy import select, join, and_, text
import logging
import ast
import boto3
import random
from botocore.client import Config
log = logging.getLogger(__name__)

def _get_action(action, context_dict, data_dict):
    return toolkit.get_action(action)(context_dict, data_dict)

def get_random_resource_field(res_id):
    try:
        resource_fields = _get_action(u'datastore_search', None, {
                u'resource_id': res_id,
                u'limit': 0
            }
        )
        return resource_fields.get('fields')[random.randint(0, len(resource_fields.get('fields')) - 1)]
    except Exception as e:
        pass

    return []


def get_datastore_resource_fields(res_id):
    try:
        resource_fields = _get_action(u'datastore_search', None, {
                u'resource_id': res_id,
                u'limit': 0
            }
        )

        return sorted([field['id'] for field in resource_fields.get('fields', [])])
    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        pass

    return []


def get_resources_list(dataset_id, has_data_dict=True):
    context = {}
    # Using package_show instead of package_search
    pkg = _get_action('package_show', context, {'id':dataset_id})
    resources = pkg['resources']
    if not has_data_dict:
        return resources
    filtered_resource = []
    # Filtering resources having data dictionary
    for res in resources:
        try:
            rec = _get_action(u'datastore_search',None, {
                    u'resource_id': res['id'],
                    u'limit': 0
                }
            )
            filtered_resource.append(res)
        except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
            pass
    sorted_resources = sorted(filtered_resource, key=lambda x: x['created'], reverse=True)
    return sorted_resources


def get_resource_list_dropdown(dataset_id):

    resources = get_resources_list(dataset_id)

    return [{'name': x['id'], 'value': x['name']} for x in resources]


import json
def get_dataset_data_dictionary(pkg_dict):
    '''Returns an array of fields as per fields attribute in Table Schema.

    We expect packages / datasets to have a field (in extras) called
    'tableschema' with Frictionless Data Table Schema.
    '''
    if not pkg_dict:
        return []
    tableschema = [ f['value'] for f in pkg_dict.get('extras', []) if f['key'] == 'tableschema' ]
    if tableschema:
        return json.loads(tableschema[0])['fields']
    else:
        return []

import ast
def get_resource_data_dictionary(pkg_dict):
    '''Returns an array of fields as per fields attribute in Table Schema.

    We expect resources to have a called
    'schema' with Frictionless Data Table Schema.
    '''
    try:
        if not pkg_dict:
            return []
        tableschema = pkg_dict.get('schema', [])
        if tableschema:
            try:
                return json.loads(tableschema)['fields']
            except:
                return ast.literal_eval(tableschema).get('fields')
        else:
            return []
    except Exception as ex:
        log.error("get_resource_data_dictionary - {}".format(str(ex)))


def resource_convert_schema(schema):
    try:
        result = ast.literal_eval(schema)
        fields = [field['name'] for field in result.get('fields', [])]
        log.info("fields: {}".format(fields))
        return sorted(fields)
    except Exception as ex:
        log.error("Error converting schema to list - {}".format(str(ex)))
        return []

def resource_view_get_fields(resource):
    '''Returns sorted list of text and time fields of a datastore resource.'''
    try:
        data = {
            'resource_id': resource['bq_table_name'],
            'limit': 0
        }
        log.warning("resource_view_get_fields - data: {}".format(data))

        result = logic.get_action('datastore_search')({}, data)

        fields = [field['id'] for field in result.get('fields', [])]

        return sorted(fields)
    except Exception as ex:
        log.error("resource_view_get_fields - {}".format(str(ex)))
        return []

def get_latest_themes():
    context = {}
    themes = _get_action('organization_list', context, {'all_fields': True})[:5]
    themes.sort(key=lambda x: x['created'], reverse=True)

    return themes

def get_themes():
    context = {}
    themes = _get_action('organization_list', context, {'all_fields': True})
    return themes

def get_latest_datasets():
    context = {}
    data_dict = {
        'sort': 'metadata_created desc',
        'rows': 5,
        'facet': False
    }

    datasets = _get_action('package_search', context, data_dict)['results']

    return datasets

def get_latest_resources():
    private_resource_dict= '%\\\\"level\\\\": \\\\"public\\\\"%'
    j_statement = join(model.Resource, model.Package, model.Package.id == model.Resource.package_id)
    foi_group = model.Group.get('freedom-of-information-disclosure-log')
    sql = select([
        model.Resource.id, 
        model.Resource.name, 
        model.Resource.url, 
        model.Resource.format,
        model.Resource.description, 
        model.Resource.size, 
        model.Resource.last_modified,
        model.Resource.extras,
        model.Resource.created,
        model.Resource.package_id,
        text("(CASE WHEN RESOURCE.last_modified <> RESOURCE.created THEN \
        RESOURCE.last_modified ELSE RESOURCE.created END ) AS latest")
    ]).select_from(j_statement) \
    .where(
        and_(model.Package.state == 'active',  
        model.Package.private == False,
        model.Package.owner_org != foi_group.id,
        model.Resource.state == 'active',
        text("(resource.extras ILIKE \'%s\' or resource.extras ILIKE \'%s\') " % (private_resource_dict, '%{level: public}%' ))
        )
    ).order_by("latest DESC").limit(5)
    q_result = model.Session.execute(sql).fetchall()
    resource_dict = []
    for row in q_result:
        resource_dict.append(table_dictize(row, { 'model': model, 'user': '' }))
    return resource_dict

def get_cookie_control_config():

        cookie_control_config = {}

        api_key = config.get(
            'ckanext.nhs.cc.api_key', '')
        cookie_control_config['api_key'] = api_key

        license_type = config.get(
            'ckanext.nhs.cc.license_type', '')
        cookie_control_config['license_type'] = license_type

        popup_position = config.get(
            'ckanext.nhs.cc.popup_position', '')
        cookie_control_config['popup_position'] = popup_position

        theme_color = config.get(
            'ckanext.nhs.cc.theme_color', '')
        cookie_control_config['theme_color'] = theme_color

        initial_state = config.get(
            'ckanext.nhs.cc.initial_state', '')
        cookie_control_config['initial_state'] = initial_state

        return cookie_control_config

def get_googleanalytics_config():

    googleanalytics_config = {}

    googleanalytics_id = config.get(
        'googleanalytics.id', '')
    googleanalytics_config['googleanalytics_id'] = googleanalytics_id

    return googleanalytics_config

def get_dataset_report_type():
    report = [
        'Data download problem or error',
        'API problem or error',
        'Missing or incorrect data',
        'Functionality issue',
        'Other'
    ]
    return report


def API_enabled(pkg):
    try:
        upload_to_bigquery = pkg.get('upload_to_bigquery', True)
        return toolkit.asbool(upload_to_bigquery)
    except:
        return True

def get_foi_org_id():
    try:
        foi_group = model.Group.get('freedom-of-information-disclosure-log')
        return foi_group.id
    except:
        return None
    
def get_recaptcha_site_key():
    try:
        return config.get('ckanext.nhs.recaptcha_site_key', '')
    except:
        return None


def get_signed_url(url):
    endpoint_url = config.get('ckanext.cloudflare.endpoint', '')
    access_id = config.get('ckanext.cloudflare.access_id', '')
    secret = config.get('ckanext.cloudflare.access_key', '')
    s3_client = boto3.client('s3', endpoint_url=endpoint_url, aws_access_key_id=access_id, aws_secret_access_key=secret, config=Config(signature_version='s3v4'))

    # Extract the  (bucket name) and path (object key)
    object_key =url.split('cloudflarestorage.com/')[-1]
    bucket = object_key.split('/')[0]
    filename = object_key.split('/')[-1]
    key = object_key.split(bucket+'/')[-1]
    try:
        url = s3_client.generate_presigned_url(
                ClientMethod='get_object',
                    Params={
                    'Bucket':bucket,
                    'Key': key,
                    'ResponseContentDisposition':'filename='+filename
                    }
                )
        return url
    except Exception as e:
        pass


def get_config_value(key, default=None):
    return toolkit.config.get(key, default)


def get_resource_row_count(resource):
    context = {"ignore_auth": True}
    bq_table_name = resource.get('bq_table_name')
    result = 0

    if not bq_table_name:
        return result

    data_dict = {
        'resource_id': resource['bq_table_name'],
        'limit': 0
    }

    try:
        resource = _get_action('datastore_search', context, data_dict)
        return resource['total']

    except Exception as e:
        log.error("Error getting resource row count: {}".format(str(e)))

    return result
