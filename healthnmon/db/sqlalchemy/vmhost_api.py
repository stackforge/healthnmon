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
from healthnmon.db.sqlalchemy import virtualswitch_api, vm_api,\
    storagevolume_api


LOG = logging.getLogger(__name__)


def _get_deleted_vSwitches(inv_switch_id_list, db_Switches, epoch_time):
    to_be_deleted_switches = []
    for old_switch in db_Switches:
        if old_switch.get_id() not in inv_switch_id_list:
            old_switch.set_deletedEpoch(epoch_time)
            old_switch.set_deleted(True)
            to_be_deleted_switches.append(old_switch)
    return to_be_deleted_switches


def _get_deleted_portgroups(inv_pgroup_id_list, db_pgroups,
                            epoch_time, res_id):
    to_be_deleted_pgroups = []
    for old_pgroup in db_pgroups:
        if old_pgroup.get_id() not in inv_pgroup_id_list:
            if res_id == old_pgroup.get_virtualSwitchId():
                old_pgroup.set_deletedEpoch(epoch_time)
                old_pgroup.set_deleted(True)
                to_be_deleted_pgroups.append(old_pgroup)
    return to_be_deleted_pgroups


def __vm_host_set_virtualMachineIds(vmhosts, vmIdsRes):
    vmIdDict = {}
    for row in vmIdsRes:
        hostId = row[0]
        vmId = row[1]
        if hostId not in vmIdDict:
            vmIdDict[hostId] = []
        vmIdDict[hostId].append(vmId)
    for vmhost in vmhosts:
        if vmhost.get_id() in vmIdDict:
            vmhost.set_virtualMachineIds(vmIdDict.get(vmhost.get_id()))


def __vm_host_set_storageVolumeIds(vmhosts, volIdsRes):
    volIdDict = {}
    for row in volIdsRes:
        hostId = row[0]
        volId = row[1]
        if hostId not in volIdDict:
            volIdDict[hostId] = []
        volIdDict[hostId].append(volId)
    for vmhost in vmhosts:
        if vmhost.get_id() in volIdDict:
            vmhost.set_storageVolumeIds(volIdDict.get(vmhost.get_id()))


def vm_host_save(context, vmhost):
    """This API will create or update a VmHost object and its
    associations to DB. For the update to be working the VMHost
    object should have been one returned by DB API. Else it will
    be considered as a insert.
        Parameters:
        vmhost - VmHost type object to be saved
        context - nova.context.RequestContext object
    """

    if vmhost is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        vmhosts = vm_host_get_by_ids(context, [vmhost.id])
        deleted_host_portgroups = []
        if vmhosts:
            vmhost.set_createEpoch(vmhosts[0].get_createEpoch())
            vmhost.set_lastModifiedEpoch(epoch_time)
            existingVSwitches = vmhosts[0].get_virtualSwitches()
            "Dict to store switch epoch against switchid"
            switchDict_Epoch = {}
            for existingVSwitch in existingVSwitches:
                switchDict_Epoch[existingVSwitch.get_id()] = \
                    existingVSwitch.get_createEpoch()
            existing_host_portgroups = vmhosts[0].get_portGroups()
            pGroupDict = {}
            for existingPortGroup in existing_host_portgroups:
                pGroupDict[existingPortGroup.get_id()] = \
                    existingPortGroup.get_createEpoch()
            vSwitches = vmhost.get_virtualSwitches()
            newSwitchList = []
            existing_switch_PortGroups = []
            for vSwitch in vSwitches:
                switchId = vSwitch.get_id()
                db_switch = \
                    virtualswitch_api.virtual_switch_get_by_ids(context,
                                                                [switchId])
                if len(db_switch) > 0:
                    existing_switch_PortGroups = db_switch[0].get_portGroups()
                newSwitchList.append(switchId)
                if switchId in switchDict_Epoch:
                    vSwitch.set_createEpoch(switchDict_Epoch[switchId])
                    vSwitch.set_lastModifiedEpoch(epoch_time)
                else:
                    vSwitch.set_createEpoch(epoch_time)
                vs_portGroups = vSwitch.get_portGroups()
                vs_newportgroupList = []
                for vs_portGroup in vs_portGroups:
                    portId = vs_portGroup.get_id()
                    vs_newportgroupList.append(portId)
                    vs_portGroup.set_virtualSwitchId(switchId)
                    if portId in pGroupDict:
                        vs_portGroup.set_createEpoch(pGroupDict[portId])
                        vs_portGroup.set_lastModifiedEpoch(epoch_time)
                    else:
                        vs_portGroup.set_createEpoch(epoch_time)

                # Get the deleted port groups and set the deleted flag as true
                # and deletedEpoch value."
                deleted_portgroups = _get_deleted_portgroups(
                    vs_newportgroupList,
                    existing_switch_PortGroups,
                    epoch_time, switchId)
                for deleted_portgroup in deleted_portgroups:
                    vSwitch.add_portGroups(deleted_portgroup)
                    deleted_host_portgroups.append(deleted_portgroup)

            # Get the deleted virtual switches and set the deleted
            # flag as true and deletedEpoch value."
            deleted_switches = _get_deleted_vSwitches(newSwitchList,
                                                      existingVSwitches,
                                                      epoch_time)
            for deleted_switch in deleted_switches:
                deleted_pgs = deleted_switch.get_portGroups()
                for deleted_pg in deleted_pgs:
                    deleted_pg.deleted = True
                    deleted_pg.set_deletedEpoch(epoch_time)
                    deleted_host_portgroups.append(deleted_pg)
                vmhost.add_virtualSwitches(deleted_switch)

            portGroups = vmhost.get_portGroups()
            newportgroupList = []
            for portGroup in portGroups:
                portId = portGroup.get_id()
                newportgroupList.append(portId)
                if portId in pGroupDict:
                    portGroup.set_createEpoch(pGroupDict[portId])
                    portGroup.set_lastModifiedEpoch(epoch_time)
                else:
                    portGroup.set_createEpoch(epoch_time)
            # Add the deleted port groups which was appended
            # during virtualswitch."
            for deleted_pg in deleted_host_portgroups:
                vmhost.add_portGroups(deleted_pg)
        else:
            vmhost.set_createEpoch(epoch_time)
            # Add the createEpcoh to the added virtualSwitches
            vSwitches = vmhost.get_virtualSwitches()
            for vSwitch in vSwitches:
                vSwitch.set_createEpoch(epoch_time)
            # Add the createEpcoh to the added portGroups
            portGroups = vmhost.get_portGroups()
            for portGroup in portGroups:
                portGroup.set_createEpoch(epoch_time)
        __save_and_expunge(session, vmhost)
    except Exception:
        LOG.exception(_('error while adding vmhost'))
        raise
    finally:
        __cleanup_session(session)


def vm_host_get_by_ids(context, ids):
    """This API will return a list of VmHost objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        vmhosts = session.query(VmHost).filter(
            and_(VmHost.id.in_(ids),
                 or_(VmHost.deleted == False,
                     VmHost.deleted == None))).\
            options(joinedload('cost')).\
            options(joinedload('os')).\
            options(joinedload_all('virtualSwitches.portGroups.cost')).\
            options(joinedload_all('portGroups.cost')).\
            options(joinedload('ipAddresses')).\
            options(joinedload_all('virtualSwitches.subnets')).\
            options(joinedload_all('virtualSwitches.networks')).\
            options(joinedload_all('virtualSwitches.cost')).\
            all()

        # Populate virtualMachineIds
        vmIdsRes = session.query(Vm.vmHostId, Vm.id).\
            filter(Vm.vmHostId.in_(ids)).\
            filter(or_(Vm.deleted == False, Vm.deleted == None)).\
            all()
        __vm_host_set_virtualMachineIds(vmhosts, vmIdsRes)

        # Populate storageVolumeIds

        volIdsRes = session.query(
            HostMountPoint.vmHostId,
            HostMountPoint.storageVolumeId).filter(
                HostMountPoint.vmHostId.in_(ids)).all()
        __vm_host_set_storageVolumeIds(vmhosts, volIdsRes)
        return vmhosts
    except Exception:
        LOG.exception(_('error while obtaining host'))
        raise Exception('VmHost_get_by_id exception')
    finally:
        __cleanup_session(session)


def vm_host_get_all(context):
    """This API will return a list of all the VmHost objects present in DB
    Parameters:
        context - nova.context.RequestContext object
    """

    session = None
    try:
        session = nova_session.get_session()
        vmhosts = session.query(VmHost).filter(
            or_(VmHost.deleted == False, VmHost.deleted == None)).\
            options(joinedload('cost')).\
            options(joinedload('os')).\
            options(joinedload_all('virtualSwitches.portGroups.cost')).\
            options(joinedload_all('portGroups.cost')).\
            options(joinedload('ipAddresses')).\
            options(joinedload_all('virtualSwitches.subnets')).\
            options(joinedload_all('virtualSwitches.networks')).\
            options(joinedload_all('virtualSwitches.cost')).\
            all()

# options(joinedload_all('localDisks.mountPoints')).\
        # Populate virtualMachineIds
        vmIdsRes = session.query(Vm.vmHostId, Vm.id).\
            filter(or_(Vm.deleted == False, Vm.deleted == None)).all()
        __vm_host_set_virtualMachineIds(vmhosts, vmIdsRes)

        # Populate storageVolumeIds
        volIdsRes = session.query(HostMountPoint.vmHostId,
                                  HostMountPoint.storageVolumeId).all()
        __vm_host_set_storageVolumeIds(vmhosts, volIdsRes)
        return vmhosts
    except Exception:
        LOG.exception(_('error while obtaining hosts'))
        raise Exception('VmHost_get_all exception')
    finally:
        __cleanup_session(session)


def vm_host_delete_by_ids(context, ids):
    """This API will delete VmHost objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        vmhosts = vm_host_get_by_ids(context, ids)
        delete_epoch_time = get_current_epoch_ms()
        for host in vmhosts:
            vmid_tuples = \
                session.query(Vm.id).filter(
                    and_(Vm.vmHostId.in_(ids),
                         or_(Vm.deleted == False,
                             Vm.deleted == None))).all()
            vmIds = []
            for vmid_tuple in vmid_tuples:
                vmid = vmid_tuple[0]
                vmIds.append(vmid)
            vm_api.vm_delete_by_ids(context, vmIds)
            # StorageVolume deletion
            # Loop thru each of the Storage Volumes and check
            # whether it has this host attached to its mount point.
            storageIds = host.get_storageVolumeIds()
            storageObj = storagevolume_api.\
                storage_volume_get_by_ids(context, storageIds)
            for storage in storageObj:
                mountPoints = storage.get_mountPoints()
                # If this relation found then create a new list
                # of mount points and
                # add these to the storage
                newMountPoints = []
                for mountPoint in mountPoints:
                    hostId = mountPoint.get_vmHostId()
                    if host.id != hostId:
                        newMountPoints.append(mountPoint)
                storage.set_mountPoints(newMountPoints)
                __save_and_expunge(session, storage)

            vSwitches = host.get_virtualSwitches()
            for vSwitch in vSwitches:
                portGroups = vSwitch.get_portGroups()
                for portGroup in portGroups:
                    portGroup.set_deleted(True)
                    portGroup.set_deletedEpoch(delete_epoch_time)
                vSwitch.set_deleted(True)
                vSwitch.set_deletedEpoch(delete_epoch_time)

            portGroups = host.get_portGroups()
            for portGroup in portGroups:
                portGroup.set_deleted(True)
                portGroup.set_deletedEpoch(delete_epoch_time)
            # Finally delete the host
            host.set_deleted(True)
            host.set_deletedEpoch(delete_epoch_time)
            __save_and_expunge(session, host)
    except Exception:
        LOG.exception(_('error while deleting host'))
        raise
    finally:
        __cleanup_session(session)


def _load_deleted_objects(session, vmhosts):
    for host in vmhosts:
        deleted_host_vs = session.query(VirtualSwitch).\
            filter(and_(VirtualSwitch.deleted == True,
                        VirtualSwitch.vmHostId == host.get_id())).\
            options(joinedload('cost')).\
            options(joinedload('networks')).\
            options(joinedload('subnets')).all()
        deleted_host_pgs = []
        for vsd in deleted_host_vs:
            host.add_virtualSwitches(vsd)
        for vs in host.get_virtualSwitches():
            vs_id = vs.get_id()
            deleted_vs_pg = session.query(PortGroup).\
                filter(and_(PortGroup.deleted == True,
                            PortGroup.virtualSwitchId == vs_id)).\
                options(joinedload('cost')).all()
            for pg in deleted_vs_pg:
                vs.add_portGroups(pg)
                deleted_host_pgs.append(pg)
        for deleted_host_pg in deleted_host_pgs:
            host.add_portGroups(deleted_host_pg)


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
    session = None
    deleted_val = None
    # Make a copy of the filters dictionary to not effect caller's use of it.
    if filters is not None and 'deleted' in filters:
        vm_host_filters = filters.copy()
        deleted_val = vm_host_filters.pop('deleted')

    try:
        session = nova_session.get_session()
        filtered_query = _create_filtered_ordered_query(session,
                                                        VmHost,
                                                        filters=filters,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)
        vmhosts = filtered_query.options(joinedload('cost')).\
            options(joinedload('os')).\
            options(joinedload_all('virtualSwitches.portGroups.cost')).\
            options(joinedload_all('portGroups.cost')).\
            options(joinedload('ipAddresses')).\
            options(joinedload_all('virtualSwitches.subnets')).\
            options(joinedload_all('virtualSwitches.networks')).\
            options(joinedload_all('virtualSwitches.cost')).all()
        # Populate virtualMachineIds
        if deleted_val and deleted_val == 'true':
            _load_deleted_objects(session, vmhosts)
            vmIdsRes = session.query(
                Vm.vmHostId, Vm.id).filter(Vm.deleted == True).all()
        else:
            vmIdsRes = session.query(
                Vm.vmHostId, Vm.id).filter(or_(Vm.deleted == False,
                                               Vm.deleted == None)).all()
        __vm_host_set_virtualMachineIds(vmhosts, vmIdsRes)
        # Populate storageVolumeIds
        volIdsRes = session.query(HostMountPoint.vmHostId,
                                  HostMountPoint.storageVolumeId).all()
        __vm_host_set_storageVolumeIds(vmhosts, volIdsRes)
        return vmhosts
    except Exception:
        LOG.exception(_('Error while obtaining hosts'))
        raise
    finally:
        __cleanup_session(session)
