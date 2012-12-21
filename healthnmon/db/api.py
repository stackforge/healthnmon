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
Defines interface for healthnmon DB access.
Uses underlying SQL alchemy layer which is dynamically loaded.
"""

from nova.openstack.common import cfg
from nova import utils
from nova.openstack.common import cfg

db_opts = [
    cfg.StrOpt('healthnmon_db_backend',
               default='sqlalchemy',
               help='The backend to use for db'),
]

CONF = cfg.CONF
CONF.register_opts(db_opts)

IMPL = utils.LazyPluggable('healthnmon_db_backend',
                           sqlalchemy='healthnmon.db.sqlalchemy.api')


#################################################

def vm_host_save(context, vmhost):
    """This API will create or update a VmHost object and
    its associations to DB. For the update to be working the
    VMHost object should have been one returned by DB API.
    Else it will be considered as a insert.
        Parameters:
        vmhost - VmHost type object to be saved
        context - nova.context.RequestContext object
    """

    return IMPL.vm_host_save(context, vmhost)


def vm_host_get_by_ids(context, ids):
    """This API will return a list of VmHost objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """

    return IMPL.vm_host_get_by_ids(context, ids)


def vm_host_get_all(context):
    """This API will return a list of all the VmHost objects present in DB
    Parameters:
        context - nova.context.RequestContext object
    """

    return IMPL.vm_host_get_all(context)


def vm_host_delete_by_ids(context, ids):
    """This API will delete VmHost objects and its associations to DB.
    Parameters:
        ids - ids for VmHost objects to be deleted
        context - nova.context.RequestContext object
    """

    return IMPL.vm_host_delete_by_ids(context, ids)


def vm_host_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the vm_hosts that match all filters and sorted with sort_key.
        Deleted rows will be returned by default,
        unless there's a filter that says
        otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of VmHost model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'connectionState':'Connected',
                      'name':['n1', 'n2']} will filter as
                      connectionState = 'Connected' AND name in ('n1', 'n2')
                      Special filter :
                          changes-since : long value - time in epoch ms
                                          Gets the hosts changed or
                                          deleted after the specified time
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction,
            desc for descending sort direction
        Returns:
            list of vm_hosts that match all filters and sorted with sort_key
    """
    return IMPL.vm_host_get_all_by_filters(context,
                                           filters, sort_key, sort_dir)


#################################################


def vm_save(context, vm):
    """This API will create or update a Vm object and its associations to DB.
    For the update to be working the VM object should have been one returned
    by DB API. Else it will be considered as a insert.
    Parameters:
        vm - Vm type object to be saved
        context - nova.context.RequestContext object
    """

    return IMPL.vm_save(context, vm)


def vm_get_by_ids(context, ids):
    """This API will return a list of Vm objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """

    return IMPL.vm_get_by_ids(context, ids)


def vm_get_all(context):
    """This API will return a list of all the Vm objects present in DB
    Parameters:
        context - nova.context.RequestContext object
    """

    return IMPL.vm_get_all(context)


def vm_delete_by_ids(context, ids):
    """This API will delete  Vms object and its associations to DB.
    Parameters:
        ids - ids for Vm objects to be deleted
        context - nova.context.RequestContext object
    """

    return IMPL.vm_delete_by_ids(context, ids)


def vm_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the vms that match all filters and sorted with sort_key.
        Deleted rows will be returned by default, unless
        there's a filter that says
        otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of Vm model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'powerState':'ACTIVE', 'name':['n1', 'n2']}
                      will filter as
                      powerState = 'ACTIVE' AND name in ('n1', 'n2')
                      Special filter :
                          changes-since : long value - time in epoch ms
                                          Gets the Vms changed or deleted
                                          after the specified time
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction,
            desc for descending sort direction
        Returns:
            list of vms that match all filters and sorted with sort_key
    """
    return IMPL.vm_get_all_by_filters(context, filters, sort_key, sort_dir)


#################################################

def storage_volume_save(context, storagevolume):
    """This API will create or update a StorageVolume object and
    its associations to DB. For the update to be working the
    storagevolume object should have been one returned by DB API.
    Else it will be considered as a insert.
    Parameters:
        storagevolume - StorageVolume type object to be saved
        context - nova.context.RequestContext object
    """

    return IMPL.storage_volume_save(context, storagevolume)


def storage_volume_get_by_ids(context, ids):
    """This API will return a list of StorageVolume objects
    which corresponds to ids
    Parameters:
            ids - List of StorageVolume ids
            context - nova.context.RequestContext object
    """

    return IMPL.storage_volume_get_by_ids(context, ids)


def storage_volume_get_all(context):
    """This API will return a list of all the StorageVolume
    objects present in Db
    Parameters:
        context - nova.context.RequestContext object
    """

    return IMPL.storage_volume_get_all(context)


def storage_volume_delete_by_ids(context, ids):
    """This API will delete  Volume objects and its associations to DB.
    Parameters:
        ids - ids for Volumes objects to be deleted
        context - nova.context.RequestContext object
    """

    return IMPL.storage_volume_delete_by_ids(context, ids)


def storage_volume_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the storage volumes that match all filters
        and sorted with sort_key.
        Deleted rows will be returned by default,
        unless there's a filter that says
        otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of StorageVolume model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'size':1024, 'name':['vol1', 'vol2']}
                      will filter as
                      size = 1024 AND name in ('vol1', 'vol2')
                      Special filter :
                          changes-since : long value - time in epoch ms
                                          Gets the volumes changed or
                                          deleted after the specified time
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction,
            desc for descending sort direction
        Returns:
            list of storage volumes that match all filters
            and sorted with sort_key
    """
    return IMPL.storage_volume_get_all_by_filters(context,
                                                  filters, sort_key, sort_dir)


# ====== VirtualSwitc APIs ===============


def virtual_switch_save(context, virtual_switch):
    """This API will create or update a VirtualSwitch object and
    its associations to DB. For the update to be working the
    VirtualSwitch object should have been one returned by DB API.
    Else it will be considered as a insert.
    Parameters:
        virtual_switch - VirtualSwitch type object to be saved
        context - nova.context.RequestContext object
    """

    return IMPL.virtual_switch_save(context, virtual_switch)


def virtual_switch_get_by_ids(context, ids):
    """This API will return a list of VirtualSwitch
    objects which corresponds to ids
    Parameters:
            ids - List of VirtualSwitch ids
            context - nova.context.RequestContext object
    """

    return IMPL.virtual_switch_get_by_ids(context, ids)


def virtual_switch_get_all(context):
    """This API will return a list of all the VirtualSwitch
    objects present in DB
    Parameters:
        context - nova.context.RequestContext object
    """

    return IMPL.virtual_switch_get_all(context)


def virtual_switch_delete_by_ids(context, ids):
    """This API will delete  VirtualSwitch objects and its associations to DB.

        Parameters:
        ids - ids for VirtualSwitch objects to be deleted
        context - nova.context.RequestContext object
    """

    return IMPL.virtual_switch_delete_by_ids(context, ids)


def virtual_switch_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the virtual_switch that match all filters
        and sorted with sort_key.
        Deleted rows will be returned by default,
        unless there's a filter that says
        otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of VirtualSwitch model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'switchType':'abc', 'name':['n1', 'n2']}
                      will filter as
                      switchType = 'abc' AND name in ('n1', 'n2')
                      Special filter :
                          changes-since : long value - time in epoch ms
                                          Gets the virtual switches
                                          changed or deleted after
                                          the specified time
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction,
            desc for descending sort direction
        Returns:
            list of virtual_switch that match all filters
            and sorted with sort_key
    """
    return IMPL.virtual_switch_get_all_by_filters(context,
                                                  filters,
                                                  sort_key,
                                                  sort_dir)


# ====== PortGroup APIs ===============


def port_group_save(context, port_group):
    """This API will create or update a PortGroup and its associations to DB.
    For the update to be working the port group object should have been one
    returned by DB API. Else it will be considered as a insert.

        Parameters:
        port group - PortGroup type object to be saved
        context - nova.context.RequestContext object
    """

    return IMPL.port_group_save(context, port_group)


def port_group_get_by_ids(context, ids):
    """This API will return a list of PortGroup which corresponds to ids

        Parameters:
            ids - List of PortGroup ids
            context - nova.context.RequestContext object
    """

    return IMPL.port_group_get_by_ids(context, ids)


def port_group_get_all(context):
    """This API will return a list of all the  PortGroup objects present in DB

    Parameters:
        context - nova.context.RequestContext object
    """

    return IMPL.port_group_get_all(context)


def port_group_delete_by_ids(context, ids):
    """This API will delete PortGroup objects and its associations to DB.

        Parameters:
        ids - ids for PortGroup objects to be deleted
        context - nova.context.RequestContext object
    """

    return IMPL.port_group_delete_by_ids(context, ids)


# ====== Subnet APIs ===============

def subnet_save(context, subnet):
    """This API will create or update a Subnet object and its associations
    to DB. For the update to be working the Subnet object should have been
    one returned by DB API. Else it will be considered as a insert.

        Parameters:
        subnet - Subnet type object to be saved
        context - nova.context.RequestContext object
    """

    return IMPL.subnet_save(context, subnet)


def subnet_get_by_ids(context, ids):
    """This API will return a list of Subnet objects which corresponds to ids

        Parameters:
            ids - List of Subnet ids
            context - nova.context.RequestContext object
    """

    return IMPL.subnet_get_by_ids(context, ids)


def subnet_get_all(context):
    """This API will return a list of all the Subnet objects present in DB

    Parameters:
        context - nova.context.RequestContext object
    """

    return IMPL.subnet_get_all(context)


def subnet_delete_by_ids(context, ids):
    """This API will delete  Subnet objects and its associations to DB.

        Parameters:
        ids - ids for Subnet objects to be deleted
        context - nova.context.RequestContext object
    """

    return IMPL.subnet_delete_by_ids(context, ids)


def subnet_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the subnet that match all filters and sorted with sort_key.
        Deleted rows will be returned by default,
        unless there's a filter that says
        otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of Subnet model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'isPublic':True, 'name':['n1', 'n2']}
                      will filter as
                      isPublic = True AND name in ('n1', 'n2')
                      Special filter :
                          changes-since : long value - time in epoch ms
                                          Gets the subnets changed or
                                          deleted after the specified time
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction,
            desc for descending sort direction
        Returns:
            list of subnet that match all filters and sorted with sort_key
    """
    return IMPL.subnet_get_all_by_filters(context, filters, sort_key, sort_dir)
