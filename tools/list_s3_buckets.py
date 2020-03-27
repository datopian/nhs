# -*- coding: utf-8 -

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

import boto3
import datapackage

def get_amazon_credentials(aws_string):
    '''
        Get the amazon s3 credentials from CKAN config file
    '''
    aws_credentials = config.get('ckanext.nhs.' + aws_string)
    return aws_credentials


def get_bucket_name():
    bucket_name = config.get('ckanext.nhs.bucket_name')
    return bucket_name


def connect_to_s3():
    aws_access_key_id = get_amazon_credentials('aws_access_key_id')
    aws_secret_access_key = get_amazon_credentials('aws_secret_access_key')

    s3 = boto3.resource('s3',
                        aws_access_key_id = aws_access_key_id,
                        aws_secret_access_key = aws_secret_access_key)
    return s3


def list_bucket_resources(s3, bucket_name):
    response = s3.buckets.all()

    for my_bucket in response:
        bn = my_bucket.name

        if bn == bucket_name:
            for my_bucket_object in my_bucket.objects.all():
                print(my_bucket_object)