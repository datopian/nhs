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
        from tools import list_s3_buckets

        s3 = list_s3_buckets.connect_to_s3()
        bucket_name = list_s3_buckets.get_bucket_name()

        if bucket_name is None:
            print ('Please provide a bucket name in your configuration file')
        else:
            list_s3_buckets.list_bucket_resources(s3, bucket_name)