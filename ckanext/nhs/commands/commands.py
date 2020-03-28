from __future__ import print_function

import sys
from pprint import pprint
import re
import fnmatch
import os
import json
from ckanext import nhs

from ckan import model
from ckan.logic import get_action
from ckan.plugins import toolkit

from ckan.lib.cli import CkanCommand


class Nhs(CkanCommand):
    '''
        Usage:
        nhs get_s3_resource_list
            - returns a list of all resources listed in an amazon s3 bucket
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 9
    min_args = 0

    def __init__(self, name):

        super(Nhs, self).__init__(name)


    def command(self):
        self._load_config()

        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]

        if cmd == 'get_s3_resource_list':
            self.nhs_get_s3_resource_lsit()
        else:
            print('Command {0} not recognized'.format(cmd))


    def _load_config(self):
        super(Nhs, self)._load_config()


    def nhs_get_s3_resource_lsit(self):
        '''
            Get a list of resources from an Amazon S3 bucket
        '''
        from tools import list_s3_buckets

        s3 = list_s3_buckets.connect_to_s3()
        bucket_name = list_s3_buckets.get_bucket_name()

        if bucket_name is None:
            print ('Please provide a bucket name in your configuration file')
        else:
            list_s3_buckets.list_bucket_resources(s3, bucket_name)


    def nhs_transfer_s3_google(self):
        '''
            Transfer the contents of an S3 bucket to Google Cloud
            As a reference we are using the following:
            https://cloud.google.com/storage-transfer/docs/create-manage-transfer-program

            For the S3 bucket we need:
            - bucketName: we read bucket_name from the configuration file
            - accessKeyId: we read accessKeyId from the configuration file
            - secretAccessKey: we read secretAccessKey from the configuration file

            For Google Cloud we need the following parameters:
            - google_api_key:

            For the transfer function we need the following parameters:
            - description: Transfer description
            - project_id: Your Google Cloud project ID (we can set this in the config file)
            - start_date: Date YYYY/MM/DD
            - start_time: UTC Time (24hr) HH:MM:SS
            - source_bucket: Amazon S3 Bucket name (see above)
            - access_key_id: Amazon access key (see above)
            - secret_access_key: Amazon secret key (see above)
            - sink_bucket: GCS sink bucket name (A sink is an object that lets you to specify a set of log
                           entries to export to a particular destination.)
        '''
        pass