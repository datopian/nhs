import logging
import requests
import zipfile
import os

from ckan.lib.base import BaseController, render
from ckan.plugins.toolkit import (
    ObjectNotFound, NotAuthorized, get_action, get_validator, _, request,
    abort, render, c, h
)
from ckan import logic
from ckan.common import request
from ckan.controllers.organization import OrganizationController
from flask import send_file, send_from_directory, safe_join, abort


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

    def zip_resource(self, resource_id):
        # import ipdb; ipdb.set_trace()
        try:
            import zlib
            compression = zipfile.ZIP_DEFLATED
        except:
            compression = zipfile.ZIP_STORED
        resource = logic.get_action('resource_show')({}, {'id': resource_id})
        r = requests.get(resource['url'])
        with zipfile.ZipFile('{}.zip'.format(resource['name']), 'w') as resource_zip:
            resource_zip.writestr('{}.{}'.format(resource['name'], resource['format']),
                                  r.content,
                                  compress_type=compression)

        safe_path = safe_join(os.getcwd(), '{}.zip'.format(resource['name']))
        # return safe_path
        return send_file(safe_path, as_attachment=True, mimetype='application/zip', cache_timeout=300)
        # print '==============================================================='
        # try:
        #     return send_file(safe_path, as_attachment=True, mimetype='application/zip')
        # except Exception as e:
        #     print e
        #     print '==============================================================='
        #     abort(404)

        # try:
        #     return send_from_directory(app.config["CLIENT_CSV"], filename=filename, as_attachment=True)
        # except FileNotFoundError:
        #     abort(404)


  
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
