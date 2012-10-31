# vim: tabstop=4 shiftwidth=4 softtabstop=4

#          (c) Copyright 2012 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Handles all requests relating to inventory.
"""
from healthnmon import log as logging
from nova.openstack.common import cfg
from nova.db.sqlalchemy import api as context_api
from healthnmon.db import api
from nova import rpc
from nova import flags

LOG = logging.getLogger('healthnmon.healthnmon_api')

api_opts = [
cfg.StrOpt('healthnmon_topic',
            default='healthnmon',
            help='the topic healthnmon service listen on')
    ]

FLAGS = flags.FLAGS

try:
    FLAGS.healthnmon_topic
except cfg.NoSuchOptError:
    FLAGS.register_opts(api_opts)


'''def vm_host_get_all(context):
    """ This API will make a call to db layer to fetch the list of all
        the VmHost objects.

        Parameters:
            context - nova.context.RequestContext object
    """

    return api.vm_host_get_all(context)'''


def vm_host_get_all_by_filters(context, filters, sort_key, sort_dir):
    """ This API will make a call to db layer to fetch the list of all the
        VmHost objects.
        Parameters:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of VmHost model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'connectionState':'Connected', 'name':['n1', 'n2']} will filter as
                      connectionState = 'Connected' AND name in ('n1', 'n2')
            sort_key - Field on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for descending sort direction
        Returns:
            list of vm_hosts that match all filters and sorted with sort_key
    """
    return api.vm_host_get_all_by_filters(context, filters, sort_key, sort_dir)


def vm_host_get_by_ids(context, host_ids):
    """ This API will make a call to db layer to fetch a VmHost objects which
        corresponds to ids

        Parameters:
            host_ids - List of VmHost ids
            context - nova.context.RequestContext object
    """

    return api.vm_host_get_by_ids(context, host_ids)


def storage_volume_get_by_ids(context, storagevolume_ids):
    """ This API will make a call to db layer to fetch a StorageVolume objects
        which corresponds to ids

        Parameters:
            storagevolume_ids - List of StorageVolume ids
            context - nova.context.RequestContext object
    """

    return api.storage_volume_get_by_ids(context, storagevolume_ids)


'''def storage_volume_get_all(context):
    """ This API will make a call to db layer to fetch the list of all the
        StorageVolume objects.

        Parameters:
            context - nova.context.RequestContext object
    """

    return api.storage_volume_get_all(context)'''


def storage_volume_get_all_by_filters(context, filters, sort_key, sort_dir):
    """ This API will make a call to db layer to fetch the list of all the
        StorageVolume objects.
        Parameters:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of StorageVolume model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'size':1024, 'name':['vol1', 'vol2']} will filter as
                      size = 1024 AND name in ('vol1', 'vol2')
            sort_key - Field on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for descending sort direction
        Returns:
            list of storage volumes that match all filters and sorted with sort_key
    """
    return api.storage_volume_get_all_by_filters(context, filters, sort_key, sort_dir)


def vm_get_by_ids(context, vm_ids):
    """ This API will make a call to db layer to fetch a Vm objects which
        corresponds to ids

        Parameters:
            vm_ids - List of Vm ids
            context - nova.context.RequestContext object
    """

    return api.vm_get_by_ids(context, vm_ids)


'''def vm_get_all(context):
    """ This API will make a call to db layer to fetch the list of all the
        Vm objects.
    Parameters:
        context - nova.context.RequestContext object
    """

    return api.vm_get_all(context)'''


def vm_get_all_by_filters(context, filters, sort_key, sort_dir):
    """ This API will make a call to db layer to fetch the list of all the
        VM objects.
        Parameters:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of Vm model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'powerState':'ACTIVE', 'name':['n1', 'n2']} will filter as
                      powerState = 'ACTIVE' AND name in ('n1', 'n2')
            sort_key - Field on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for descending sort direction
        Returns:
            list of vms that match all filters and sorted with sort_key
    """
    return api.vm_get_all_by_filters(context, filters, sort_key, sort_dir)


'''def subnet_get_all(context):
    """ Fetch list of subnets
    :param context: nova.context.RequestContext object
    """

    return api.subnet_get_all(context)'''


def subnet_get_all_by_filters(context, filters, sort_key, sort_dir):
    """ This API will make a call to db layer to fetch the list of all the
        Subnet objects.
        Parameters:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of Subnet model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'isPublic':True, 'name':['n1', 'n2']} will filter as
                      isPublic = True AND name in ('n1', 'n2')
            sort_key - Field on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for descending sort direction
        Returns:
            list of subnet that match all filters and sorted with sort_key
    """
    return api.subnet_get_all_by_filters(context, filters, sort_key, sort_dir)


def subnet_get_by_ids(context, subnet_ids):
    """ Fetch subnet details of the subnet ids
            Parameters:
            subnet_ids - List of subnet ids
            context - nova.context.RequestContext object
    """

    return api.subnet_get_by_ids(context, subnet_ids)


'''def virtual_switch_get_all(context):
    """ Fetch list of virtual switches
            Parameters:
            context - nova.context.RequestContext object
    """

    return api.virtual_switch_get_all(context)'''


def virtual_switch_get_all_by_filters(context, filters, sort_key, sort_dir):
    """ This API will make a call to db layer to fetch the list of all the
        VirtualSwitch objects.
        Parameters:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of VirtualSwitch model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'switchType':'abc', 'name':['n1', 'n2']} will filter as
                      switchType = 'abc' AND name in ('n1', 'n2')
            sort_key - Field on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for descending sort direction
        Returns:
            list of virtual_switch that match all filters and sorted with sort_key
    """
    return api.virtual_switch_get_all_by_filters(context, filters, sort_key, sort_dir)


def virtual_switch_get_by_ids(context, virtual_switch_ids):
    """ Fetch virtual switch details of the ids
            Parameters:
            virtual_switch_ids - List of virtual switch ids
            context - nova.context.RequestContext object
    """

    return api.virtual_switch_get_by_ids(context, virtual_switch_ids)


@context_api.require_context
def get_vm_utilization(context, vm_id):
    """ This API will fetches VM utilization from healthnmon service thru rpc

    Parameters:
        vm_id - uuid of the virtual machine.
        context - nova.context.RequestContext object
    """

    return rpc.call(context, FLAGS.healthnmon_topic,
                    {'method': 'get_vm_utilization',
                    'args': {'uuid': vm_id}})


@context_api.require_context
def get_vmhost_utilization(context, host_id):
    """ This API will fetches VM Host utilization from healthnmon service thru
        rpc call.

    Parameters:
        host_id: uuid of the vmhost.
        context - nova.context.RequestContext object
    """

    return rpc.call(context, FLAGS.healthnmon_topic,
                    {'method': 'get_vmhost_utilization',
                    'args': {'uuid': host_id}})
