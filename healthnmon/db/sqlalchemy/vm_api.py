# vim: tabstop=4 shiftwidth=4 softtabstop=4

#          (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from healthnmon.db.sqlalchemy.util import _create_filtered_ordered_query, \
    __save_and_expunge, __cleanup_session


LOG = logging.getLogger(__name__)


def vm_save(context, vm):
    """This API will create or update a Vm object and its associations to DB.
    For the update to be working the VM object should have been
    one returned by DB API. Else it will be considered as a insert.
       Parameters:
        vm - Vm type object to be saved
        context - nova.context.RequestContext object
    """

    if vm is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        vms = vm_get_by_ids(context, [vm.id])
        if vms is not None and len(vms) > 0:
            vm.set_createEpoch(vms[0].get_createEpoch())
            vm.set_lastModifiedEpoch(epoch_time)
            vmGlobalSettings = vm.get_vmGlobalSettings()
            if vmGlobalSettings is not None:
                if vms[0].get_vmGlobalSettings() is not None:
                    vmGlobalSettings.set_createEpoch(
                        vms[0].get_vmGlobalSettings().get_createEpoch())
                    vmGlobalSettings.set_lastModifiedEpoch(epoch_time)
                else:
                    vmGlobalSettings.set_createEpoch(epoch_time)
        else:
            vm.set_createEpoch(epoch_time)
            vmGlobalSettings = vm.get_vmGlobalSettings()
            if vmGlobalSettings is not None:
                vmGlobalSettings.set_createEpoch(epoch_time)
        __save_and_expunge(session, vm)
    except Exception:
        LOG.exception(_('Error while saving vm'))
        raise
    finally:
        __cleanup_session(session)


def vm_get_by_ids(context, ids):
    """This API will return a list of Vm objects which corresponds to ids

        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        vms = session.query(Vm).filter(
            and_(Vm.id.in_(ids),
                 or_(Vm.deleted == False,
                 Vm.deleted == None))).\
            options(joinedload('cost')).\
            options(joinedload('os')).\
            options(joinedload('ipAddresses')).\
            options(joinedload_all('vmNetAdapters', 'ipAdd')).\
            options(joinedload('vmScsiControllers')).\
            options(joinedload('vmDisks')).\
            options(joinedload_all('vmGenericDevices', 'properties')).\
            options(joinedload('vmGlobalSettings')).\
            options(joinedload('cpuResourceAllocation')).\
            options(joinedload('memoryResourceAllocation')).all()
        return vms
    except Exception:
        LOG.exception(_('error while obtaining Vm'))
        raise
    finally:
        __cleanup_session(session)


def vm_get_all(context):
    """This API will return a list of all the Vm objects present in DB
    Parameters:
        context - nova.context.RequestContext object
    """
    session = None
    try:
        session = nova_session.get_session()
        vms = session.query(Vm).filter(or_(Vm.deleted == False,
                                           Vm.deleted == None)).\
            options(joinedload('cost')).\
            options(joinedload('os')).\
            options(joinedload('ipAddresses')).\
            options(joinedload_all('vmNetAdapters', 'ipAdd')).\
            options(joinedload('vmScsiControllers')).\
            options(joinedload('vmDisks')).\
            options(joinedload_all('vmGenericDevices', 'properties')).\
            options(joinedload('vmGlobalSettings')).\
            options(joinedload('cpuResourceAllocation')).\
            options(joinedload('memoryResourceAllocation')).all()
        return vms
    except Exception:
        LOG.exception(_('error while obtaining Vm'))
        raise
    finally:
        __cleanup_session(session)


def vm_delete_by_ids(context, ids):
    """This API will delete Vm objects which corresponds to ids
    Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        vms = vm_get_by_ids(context, ids)
        for vm in vms:
            epoch_time = get_current_epoch_ms()
            vm.set_deletedEpoch(epoch_time)
            vm.set_deleted(True)
            vmGlobalSettings = vm.get_vmGlobalSettings()
            if vmGlobalSettings is not None:
                vmGlobalSettings.set_deletedEpoch(epoch_time)
                vmGlobalSettings.set_deleted(True)
            __save_and_expunge(session, vm)
    except Exception:

        LOG.exception(_('error while deleting vm'))
        raise
    finally:
        __cleanup_session(session)


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
    session = None
    try:
        session = nova_session.get_session()
        filtered_query = _create_filtered_ordered_query(session, Vm,
                                                        filters=filters,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)
        vms = filtered_query.\
            options(joinedload('cost')).\
            options(joinedload('os')).\
            options(joinedload('ipAddresses')).\
            options(joinedload_all('vmNetAdapters', 'ipAdd')).\
            options(joinedload('vmScsiControllers')).\
            options(joinedload('vmDisks')).\
            options(joinedload_all('vmGenericDevices', 'properties')).\
            options(joinedload('vmGlobalSettings')).\
            options(joinedload('cpuResourceAllocation')).\
            options(joinedload('memoryResourceAllocation')).all()
        return vms
    except Exception:
        LOG.exception(_('Error while obtaining Vm'))
        raise
    finally:
        __cleanup_session(session)
