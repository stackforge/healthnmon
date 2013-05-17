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

from sqlalchemy.orm import joinedload, joinedload_all
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    Vm, StorageVolume, HostMountPoint, VirtualSwitch, PortGroup, \
    Subnet
from healthnmon.db.sqlalchemy.mapper import VirtualSwitchSubnetIds
from nova.openstack.common.db.sqlalchemy import session as nova_session
from nova.db.sqlalchemy import api as context_api
from healthnmon import log as logging
from healthnmon import constants
from healthnmon.utils import get_current_epoch_ms
from healthnmon.db.sqlalchemy import vmhost_api, vm_api, storagevolume_api, \
    virtualswitch_api, portgroup_api, subnet_api


LOG = logging.getLogger(__name__)


#################################


@context_api.require_admin_context
def vm_host_save(context, vmhost):
    """This API will create or update a VmHost object and its
    associations to DB. For the update to be working the VMHost
    object should have been one returned by DB API. Else it will
    be considered as a insert.
        Parameters:
        vmhost - VmHost type object to be saved
        context - nova.context.RequestContext object
    """
    return vmhost_api.vm_host_save(context, vmhost)


@context_api.require_admin_context
def vm_host_get_by_ids(context, ids):
    """This API will return a list of VmHost objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """
    return vmhost_api.vm_host_get_by_ids(context, ids)


@context_api.require_admin_context
def vm_host_get_all(context):
    """This API will return a list of all the VmHost objects present in DB
    Parameters:
        context - nova.context.RequestContext object
    """
    return vmhost_api.vm_host_get_all(context)


@context_api.require_admin_context
def vm_host_delete_by_ids(context, ids):
    """This API will delete VmHost objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """
    return vmhost_api.vm_host_delete_by_ids(context, ids)


@context_api.require_admin_context
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
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction,
            desc for descending sort direction
        Returns:
            list of vm_hosts that match all filters and sorted with sort_key
    """
    return vmhost_api.vm_host_get_all_by_filters(context,
                                                 filters, sort_key, sort_dir)


#################################


@context_api.require_context
def vm_save(context, vm):
    """This API will create or update a Vm object and its associations to DB.
    For the update to be working the VM object should have been
    one returned by DB API. Else it will be considered as a insert.
       Parameters:
        vm - Vm type object to be saved
        context - nova.context.RequestContext object
    """
    return vm_api.vm_save(context, vm)


@context_api.require_context
def vm_get_by_ids(context, ids):
    """This API will return a list of Vm objects which corresponds to ids

        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """
    return vm_api.vm_get_by_ids(context, ids)


@context_api.require_context
def vm_get_all(context):
    """This API will return a list of all the Vm objects present in DB
    Parameters:
        context - nova.context.RequestContext object
    """
    return vm_api.vm_get_all(context)


@context_api.require_context
def vm_delete_by_ids(context, ids):
    """This API will delete Vm objects which corresponds to ids
    Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """
    return vm_api.vm_delete_by_ids(context, ids)


@context_api.require_admin_context
def vm_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the vms that match all filters and sorted with sort_key.
        Deleted rows will be returned by default, unless there's
        a filter that says otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of Vm model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'powerState':'ACTIVE', 'name':['n1', 'n2']}
                      will filter as
                      powerState = 'ACTIVE' AND name in ('n1', 'n2')
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for descending
            sort direction
        Returns:
            list of vms that match all filters and sorted with sort_key
    """
    return vm_api.vm_get_all_by_filters(context, filters, sort_key, sort_dir)


####################################################


@context_api.require_admin_context
def storage_volume_save(context, storagevolume):
    """This API will create or update a StorageVolume object and its
    associations to DB. For the update to be working the VMHost object
    should have been one returned by DB API. Else it will be considered
    as a insert.
        Parameters:
        storagevolume - StorageVolume type object to be saved
        context - nova.context.RequestContext object
    """
    return storagevolume_api.storage_volume_save(context, storagevolume)


@context_api.require_admin_context
def storage_volume_get_by_ids(context, ids):
    """This API will return a list of StorageVolume
    objects which corresponds to ids
        Parameters:
            ids - List of StorageVolume ids
            context - nova.context.RequestContext object
    """
    return storagevolume_api.storage_volume_get_by_ids(context, ids)


@context_api.require_admin_context
def storage_volume_get_all(context):
    """This API will return a list of all the StorageVolume
    objects present in DB

    Parameters:
        context - nova.context.RequestContext object
    """
    return storagevolume_api.storage_volume_get_all(context)


@context_api.require_admin_context
def storage_volume_delete_by_ids(context, ids):
    """This API will delete StorageVolume objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object (optional parameter)

    """
    return storagevolume_api.storage_volume_delete_by_ids(context, ids)


@context_api.require_admin_context
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
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc
            for descending sort direction
        Returns:
            list of storage volumes that match all filters
            and sorted with sort_key
    """
    return storagevolume_api.storage_volume_get_all_by_filters(context,
                                                               filters,
                                                               sort_key,
                                                               sort_dir)


# ====== VIrtual Switch APIs ==============

@context_api.require_admin_context
def virtual_switch_save(context, virtual_switch):
    """This API will create or update a VirtualSwitch object
    and its associations to DB. For the update to be working
    the virtual_switch object should have been one returned by DB API.
    Else it will be considered as a insert.
        Parameters:
        virtual_switch - network type object to be saved
        context - nova.context.RequestContext object (optional parameter)
    """
    return virtualswitch_api.virtual_switch_save(context, virtual_switch)


@context_api.require_admin_context
def virtual_switch_get_by_ids(context, ids):
    """This API will return a list of virtual switch objects
    which corresponds to ids

        Parameters:
            ids - List of virtual switch ids
            context - nova.context.RequestContext object (optional parameter)
    """
    return virtualswitch_api.virtual_switch_get_by_ids(context, ids)


@context_api.require_admin_context
def virtual_switch_get_all(context):
    """This API will return a list of all the
    virtual switch objects present in Db
    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """
    return virtualswitch_api.virtual_switch_get_all(context)


@context_api.require_admin_context
def virtual_switch_delete_by_ids(context, ids):
    """This API will delete virtual switch objects which corresponds to ids
        Parameters:
            ids - List of virtual switch ids
            context - nova.context.RequestContext object (optional parameter)
    """
    return virtualswitch_api.virtual_switch_delete_by_ids(context, ids)


@context_api.require_admin_context
def virtual_switch_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the virtual_switch that match all filters and
        sorted with sort_key.
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
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for
            descending sort direction
        Returns:
            list of virtual_switch that match all filters and
            sorted with sort_key
    """
    return virtualswitch_api.virtual_switch_get_all_by_filters(context,
                                                               filters,
                                                               sort_key,
                                                               sort_dir)


# ====== Port Group APIs ==============

@context_api.require_admin_context
def port_group_save(context, port_group):
    """This API will create or update a PortGroup object and
    its associations to DB. For the update to be working the
    port_group object should have been one returned by DB API.
    Else it will be considered as a insert.
        Parameters:
        port_group - port group object to be saved
        context - nova.context.RequestContext object (optional parameter)
    """
    return portgroup_api.port_group_save(context, port_group)


@context_api.require_admin_context
def port_group_get_by_ids(context, ids):
    """This API will return a list of PortGroup objects
    which corresponds to ids
        Parameters:
            ids - List of port group ids
            context - nova.context.RequestContext object (optional parameter)
    """
    return portgroup_api.port_group_get_by_ids(context, ids)


@context_api.require_admin_context
def port_group_get_all(context):
    """This API will return a list of all the PortGroup objects present in DB

    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """
    return portgroup_api.port_group_get_all(context)


@context_api.require_admin_context
def port_group_delete_by_ids(context, ids):
    """This API will delete port_group objects which corresponds to ids

        Parameters:
            ids - List of port group ids
            context - nova.context.RequestContext object (optional parameter)
    """
    return portgroup_api.port_group_delete_by_ids(context, ids)


# ====== Subnet APIs ===============


@context_api.require_admin_context
def subnet_save(context, subnet):
    """This API will create or update a Subnet object and
    its associations to DB. For the update to be working the
    subnet object should have been one returned by DB API.
    Else it will be considered as a insert.
        Parameters:
        subnet - port group object to be saved
        context - nova.context.RequestContext object (optional parameter)
    """
    return subnet_api.subnet_save(context, subnet)


@context_api.require_admin_context
def subnet_get_by_ids(context, ids):
    """This API will return a list of subnet objects which corresponds to ids

        Parameters:
            ids - List of subnet ids
            context - nova.context.RequestContext object (optional parameter)
    """
    return subnet_api.subnet_get_by_ids(context, ids)


@context_api.require_admin_context
def subnet_get_all(context):
    """This API will return a list of all the Subnet objects present in DB
    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """
    return subnet_api.subnet_get_all(context)


@context_api.require_admin_context
def subnet_delete_by_ids(context, ids):
    """This API will delete Subnets objects which corresponds to ids
        Parameters:
            ids - List of subnets ids
            context - nova.context.RequestContext object (optional parameter)

    """
    return subnet_api.subnet_delete_by_ids(context, ids)


@context_api.require_admin_context
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
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction,
            desc for descending sort direction
        Returns:
            list of subnet that match all filters and sorted with sort_key
    """
    return subnet_api.subnet_get_all_by_filters(context,
                                                filters, sort_key, sort_dir)
