# encoding: utf-8
from ckan.authz import is_authorized
from ckan.plugins import toolkit


def egress_gcp_fetch(context, data_dict):
    """Check if a user is allowed to fetch the egress

    This is permitted only to users who are allowed to create the dataset
    """
    return is_authorized('package_create', context, data_dict)
