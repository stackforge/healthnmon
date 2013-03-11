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


LOG = logging.getLogger('healthnmon.db.sqlalchemy.api')


def _create_filtered_ordered_query(session, *models, **kwargs):
    """
        Create a query on the model objects which is sorted and filtered
        Arguments:
            session - Sqlalchemy Session
            models - Model classes to be queried.
                     Filtering and ordering will be applied to the
                     first model class in list
        Keyword Arguments:
            filters - dictionary of filters to be applied
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for descending
            sort direction
        Returns:
            sqlalchemy.orm.query.Query object with all the filters and ordering
    """
    # Extract kwargs
    sort_key = kwargs.pop('sort_key', None)
    sort_dir = kwargs.pop('sort_dir', None)
    filters = kwargs.pop('filters', None)
    # Create query
    query = session.query(*models)
    # Apply filters
    primary_model = models[0]
    if filters is not None:
        # Make a copy of the filters dictionary to use going forward, as we'll
        # be modifying it and we shouldn't affect the caller's use of it.
        filters = filters.copy()
        if 'changes-since' in filters:
            try:
                changes_since_val = filters.pop('changes-since')
                changes_since = long(changes_since_val)
                lastModifiedEpoch_col = getattr(primary_model,
                                                'lastModifiedEpoch')
                deletedEpoch_col = getattr(primary_model, 'deletedEpoch')
                createEpoch_col = getattr(primary_model, 'createEpoch')
                changes_since_filter = or_(
                    lastModifiedEpoch_col > changes_since,
                    deletedEpoch_col > changes_since,
                    createEpoch_col > changes_since,)
                query = query.filter(changes_since_filter)
            except ValueError:
                LOG.warn(
                    _('Invalid value for changes-since filter : '
                        + str(changes_since_val)),
                    exc_info=True)
            except AttributeError:
                LOG.warn(
                    _('Cannot apply changes-since filter to model : '
                        + str(primary_model)),
                    exc_info=True)
        if 'deleted' in filters:
            try:
                deleted_val = filters.pop('deleted')
                deleted_col = getattr(primary_model, 'deleted')
                if deleted_val == 'true':
                    query = query.filter(deleted_col == True)
                else:
                    not_deleted_filter = or_(deleted_col == False,
                                             deleted_col == None)
                    query = query.filter(not_deleted_filter)
            except AttributeError:
                LOG.warn(
                    _('Cannot apply deleted filter to model : '
                        + str(primary_model)),
                    exc_info=True)
        # Apply other filters
        filter_dict = {}
        for key in filters.keys():
            value = filters.pop(key)
            try:
                column_attr = getattr(primary_model, key)
            except AttributeError:
                LOG.warn(
                    _('Cannot apply ' + str(key) + ' filter to model : '
                        + str(primary_model)),
                    exc_info=True)
                continue
            if primary_model.get_all_members()[key].container == 1:
                # Its a list type attribute. So use contains
                if isinstance(value, (list, tuple, set, frozenset)):
                    # Use the filter column_attr contains value[0] OR
                    # column_attr contains value[1] ...
                    or_clauses = []
                    for each_value in value:
                        clause = column_attr.contains(each_value)
                        or_clauses.append(clause)
                    query = query.filter(or_(*or_clauses))
                else:
                    query = query.filter(column_attr.contains(value))
            elif isinstance(value, (list, tuple, set, frozenset)):
                # Looking for values in a list; apply to query directly
                query = query.filter(column_attr.in_(value))
            else:
                # OK, simple exact match; save for later
                filter_dict[key] = value
        if len(filter_dict) > 0:
            query = query.filter_by(**filter_dict)
    # Apply sorting
    if sort_key is not None:
        try:
            sort_col = getattr(primary_model, sort_key)
            if sort_dir == constants.DbConstants.ORDER_DESC:
                sort_fn = desc
            else:
                # Default sort asc
                sort_fn = asc
            query = query.order_by(sort_fn(sort_col))
        except AttributeError:
            LOG.warn(
                _('Cannot apply sorting as model '
                    + str(
                  primary_model) + ' do not have field ' + str(sort_key)),
                exc_info=True)
    return query


def __save_and_expunge(session, obj):
    """Save a ORM object to db and expunge the object from session
        Parameters:
        session - Sqlalchemy Session
        obj - ORM object to be saved
    """

    session.merge(obj)
    session.flush()
    session.expunge_all()


def __cleanup_session(session):
    """Clean up session
        Parameters:
        session - Sqlalchemy Session
    """

    if session is not None:
        session.flush()
        session.expunge_all()
        session.close()


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
                db_switch = virtual_switch_get_by_ids(context, [switchId])
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


@context_api.require_admin_context
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


@context_api.require_admin_context
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


@context_api.require_admin_context
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
            vm_delete_by_ids(context, vmIds)
            # StorageVolume deletion
            # Loop thru each of the Storage Volumes and check
            # whether it has this host attached to its mount point.
            storageIds = host.get_storageVolumeIds()
            storageObj = storage_volume_get_by_ids(context, storageIds)
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


@context_api.require_context
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


@context_api.require_context
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


@context_api.require_context
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

    if storagevolume is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        storagevolumes = storage_volume_get_by_ids(context,
                                                   [storagevolume.id])
        if storagevolumes:
            storagevolume.set_createEpoch(storagevolumes[0].get_createEpoch())
            storagevolume.set_lastModifiedEpoch(epoch_time)
        else:
            storagevolume.set_createEpoch(epoch_time)
        __save_and_expunge(session, storagevolume)
    except Exception:
        LOG.exception(_('error while adding/updating  StorageVolume'))
        raise
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def storage_volume_get_by_ids(context, ids):
    """This API will return a list of StorageVolume
    objects which corresponds to ids
        Parameters:
            ids - List of StorageVolume ids
            context - nova.context.RequestContext object
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        storagevolumes = \
            session.query(
                StorageVolume).filter(
                    and_(StorageVolume.id.in_(ids),
                         or_(StorageVolume.deleted == False,
                             StorageVolume.deleted == None))).\
            options(joinedload('mountPoints')).all()
        return storagevolumes
    except Exception:
        LOG.exception(_('error while obtaining StorageVolume'))
        raise Exception('StorageVolume_get_by_id exception')
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def storage_volume_get_all(context):
    """This API will return a list of all the StorageVolume
    objects present in DB

    Parameters:
        context - nova.context.RequestContext object
    """

    session = None
    try:
        session = nova_session.get_session()
        storagevolumes = \
            session.query(
                StorageVolume).filter(
                    or_(StorageVolume.deleted == False,
                        StorageVolume.deleted == None)) \
            .options(joinedload('mountPoints')).all()
        return storagevolumes
    except Exception:
        LOG.exception(_('error while obtaining StorageVolume'))
        raise Exception('StorageVolume_get_all exception')
    finally:
        __cleanup_session(session)


def __delete_vm_storage_association(storage, context):
    vmDisks = storage.vmDisks
    if (vmDisks is not None) and (len(vmDisks) > 0):
        del vmDisks[:]


def __delete_host_storage_association(storage, context):
    try:
        hostMounts = storage.get_mountPoints()
        if len(hostMounts) > 0:
            del hostMounts[:]
    except Exception:
        LOG.exception('Error while  removing association between vmHost \
        and storageVolume')
        raise


@context_api.require_admin_context
def storage_volume_delete_by_ids(context, ids):
    """This API will delete StorageVolume objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object (optional parameter)

    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        storageVolumes = session.query(StorageVolume).\
            filter(StorageVolume.id.in_(ids)).\
            filter(or_(StorageVolume.deleted == False,
                       StorageVolume.deleted == None)).\
            options(joinedload('mountPoints')).\
            options(joinedload('vmDisks')).\
            all()
        for storageVolume in storageVolumes:
            __delete_host_storage_association(storageVolume, context)
            __delete_vm_storage_association(storageVolume, context)
            epoch_time = get_current_epoch_ms()
            storageVolume.set_deletedEpoch(epoch_time)
            storageVolume.set_deleted(True)
            __save_and_expunge(session, storageVolume)
    except Exception:
        LOG.exception(_('error while deleteing storage volume'))
        raise
    finally:
        __cleanup_session(session)


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
    session = None
    try:
        session = nova_session.get_session()
        filtered_query = _create_filtered_ordered_query(session, StorageVolume,
                                                        filters=filters,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)
        storagevolumes = filtered_query.options(
            joinedload('mountPoints')).all()
        return storagevolumes
    except Exception:
        LOG.exception(_('Error in storage_volume_get_all_by_filters'))
        raise
    finally:
        __cleanup_session(session)


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
    if virtual_switch is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        virtual_switches = virtual_switch_get_by_ids(context,
                                                     [virtual_switch.id])
        if virtual_switches:
            # Add the extracted createEpcoh and the new epoch to
            # lastModifiedEpoch to the added portGroups
            pGroupDict = {}
            for virtualswitch in virtual_switches:
                pgs = virtualswitch.get_portGroups()
                for pg in pgs:
                    pGroupDict[pg.get_id()] = pg.get_createEpoch()
            virtual_switch.set_createEpoch(
                virtual_switches[0].get_createEpoch())
            virtual_switch.set_lastModifiedEpoch(epoch_time)
            portGroups = virtual_switch.get_portGroups()
            for portGroup in portGroups:
                portId = portGroup.get_id()
                if portId in pGroupDict:
                    portGroup.set_createEpoch(pGroupDict[portId])
                    portGroup.set_lastModifiedEpoch(epoch_time)
                else:
                    portGroup.set_createEpoch(epoch_time)
        else:
            virtual_switch.set_createEpoch(epoch_time)
            for portGroup in virtual_switch.get_portGroups():
                portGroup.set_createEpoch(epoch_time)

        __save_and_expunge(session, virtual_switch)
    except Exception:
        LOG.exception(_('error while adding/updating  VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def virtual_switch_get_by_ids(context, ids):
    """This API will return a list of virtual switch objects
    which corresponds to ids

        Parameters:
            ids - List of virtual switch ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        virtualswitches = \
            session.query(VirtualSwitch).filter(
                and_(VirtualSwitch.id.in_(ids),
                     or_(VirtualSwitch.deleted == False,
                         VirtualSwitch.deleted == None))).\
            options(joinedload('cost')).\
            options(joinedload_all('portGroups.cost')).\
            options(joinedload('networks')).\
            options(joinedload('subnets')).all()
        return virtualswitches
    except Exception:
        LOG.exception(_('error while obtaining VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def virtual_switch_get_all(context):
    """This API will return a list of all the
    virtual switch objects present in Db
    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """

    session = None
    try:
        session = nova_session.get_session()
        virtualswitches = \
            session.query(VirtualSwitch).filter(
                or_(VirtualSwitch.deleted == False,
                    VirtualSwitch.deleted == None)).\
            options(joinedload('cost')).\
            options(joinedload_all('portGroups.cost')).\
            options(joinedload('networks')).\
            options(joinedload('subnets')).all()

        return virtualswitches
    except Exception:
        LOG.exception(_('error while obtaining VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def virtual_switch_delete_by_ids(context, ids):
    """This API will delete virtual switch objects which corresponds to ids
        Parameters:
            ids - List of virtual switch ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        vSwitches = virtual_switch_get_by_ids(context, ids)
        portGroupIds = \
            session.query(
                PortGroup.id).filter(and_(PortGroup.virtualSwitchId.in_(ids),
                                     or_(PortGroup.deleted == False,
                                         PortGroup.deleted == None))).all()
        pgIds = []
        for portGroupId in portGroupIds:
            pg_tuple = portGroupId[0]
            pgIds.append(pg_tuple)
        port_group_delete_by_ids(context, pgIds)
        for vSwitch in vSwitches:
            epoch_time = get_current_epoch_ms()
            vSwitch.set_deletedEpoch(epoch_time)
            vSwitch.set_deleted(True)
            __save_and_expunge(session, vSwitch)
    except Exception:
        LOG.exception(_('error while deleting the VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


def _load_deleted_switches(session, vswitches):
    for vs in vswitches:
            vs_id = vs.get_id()
            deleted_vs_pg = session.query(PortGroup).\
                filter(and_(PortGroup.deleted == True,
                            PortGroup.virtualSwitchId == vs_id)).\
                options(joinedload('cost')).all()
            for pg in deleted_vs_pg:
                vs.add_portGroups(pg)


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
    session = None
    try:
        session = nova_session.get_session()
        filtered_query = _create_filtered_ordered_query(session, VirtualSwitch,
                                                        filters=filters,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)
        virtualswitches = filtered_query.options(
            joinedload_all('portGroups.cost')).\
            options(joinedload('cost')).\
            options(joinedload('networks')).\
            options(joinedload('subnets')).all()

        if filters is not None and 'deleted' in filters:
            vs_filters = filters.copy()
            deleted_val = vs_filters.pop('deleted')
            if deleted_val and deleted_val == 'true':
                _load_deleted_switches(session, virtualswitches)
        return virtualswitches
    except Exception:
        LOG.exception(_('Error while obtaining VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


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

    if port_group is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        port_groups = port_group_get_by_ids(context, [port_group.id])
        if port_groups:
            port_group.set_createEpoch(port_groups[0].get_createEpoch())
            port_group.set_lastModifiedEpoch(epoch_time)
        else:
            port_group.set_createEpoch(epoch_time)
        __save_and_expunge(session, port_group)
    except Exception:
        LOG.exception(_('error while adding/updating  PortGroup'))
        raise
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def port_group_get_by_ids(context, ids):
    """This API will return a list of PortGroup objects
    which corresponds to ids
        Parameters:
            ids - List of port group ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        portgroups = \
            session.query(PortGroup).filter(
                and_(PortGroup.id.in_(ids),
                     or_(PortGroup.deleted == False,
                         PortGroup.deleted == None))).\
            options(joinedload('cost')).all()
        session.expunge_all()
        return portgroups
    except Exception:
        LOG.exception(_('error while obtaining PortGroup'))
        raise
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def port_group_get_all(context):
    """This API will return a list of all the PortGroup objects present in DB

    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """
    session = None
    try:
        session = nova_session.get_session()
        portgroups = \
            session.query(PortGroup).filter(
                or_(PortGroup.deleted == False,
                    PortGroup.deleted == None)).\
            options(joinedload('cost')).all()
        session.expunge_all()
        return portgroups
    except Exception:
        LOG.exception(_('error while obtaining PortGroup'))
        raise Exception('portGroup_get_all exception')
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def port_group_delete_by_ids(context, ids):
    """This API will delete port_group objects which corresponds to ids

        Parameters:
            ids - List of port group ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        portGroups = port_group_get_by_ids(context, ids)
        for portGroup in portGroups:
            epoch_time = get_current_epoch_ms()
            portGroup.set_deletedEpoch(epoch_time)
            portGroup.set_deleted(True)
            __save_and_expunge(session, portGroup)
    except Exception:
        LOG.exception(_('error while deleting the PortGroup'))
        raise
    finally:
        __cleanup_session(session)


# ====== Subnet APIs ===============
def _get_deleted_obj(inv_obj_id_list, db_obj_list, epoch_time):
    to_be_deleted_obj = []
    for db_obj in db_obj_list:
        if db_obj.get_id() not in inv_obj_id_list:
            db_obj.set_deletedEpoch(epoch_time)
            db_obj.set_deleted(True)
            to_be_deleted_obj.append(db_obj)
    return to_be_deleted_obj


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

    if subnet is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        subnets = subnet_get_by_ids(context, [subnet.id])
        if subnets:
            subnet.set_createEpoch(subnets[0].get_createEpoch())
            subnet.set_lastModifiedEpoch(epoch_time)
            # set for ipaddress
            ipaddress_existing = subnets[0].get_usedIpAddresses()
            ipadd_dict = {}
            for ipaddress in ipaddress_existing:
                ipadd_dict[ipaddress.get_id()] = ipaddress.get_createEpoch()
            usedipaddress = subnet.get_usedIpAddresses()
            usedip_id_list = []
            for usedip in usedipaddress:
                usedip_id_list.append(usedip.get_id())
                if usedip.get_id() in ipadd_dict:
                    usedip.set_createEpoch(ipadd_dict[usedip.get_id()])
                    usedip.set_lastModifiedEpoch(epoch_time)
                else:
                    usedip.set_createEpoch(epoch_time)

            # set for ipaddressRange
            ipaddress_range_existing = subnets[0].get_ipAddressRanges()
            ipaddr_dict = {}
            for ipaddress_r in ipaddress_range_existing:
                ipaddr_dict[ipaddress_r.get_id()] = ipaddress_r.\
                    get_createEpoch()
            ipaddress_range = subnet.get_ipAddressRanges()
            ip_range_id_list = []
            for ip_range in ipaddress_range:
                ip_range_id_list.append(ip_range.get_id())
                if ip_range.get_id() in ipaddr_dict:
                    ip_range.set_createEpoch(ipaddr_dict[ip_range.get_id()])
                    ip_range.set_lastModifiedEpoch(epoch_time)
                else:
                    ip_range.set_createEpoch(epoch_time)
            # if the any ipaddres is not in new subnet and present
            # in db, then update the deleteEpoch and mark as deleted

            # Get the deleted ipAddresses and ip-Ranges and set the
            # deleted flag and deletedEpoch value."
            deleted_ipAddress = _get_deleted_obj(
                usedip_id_list, ipaddress_existing, epoch_time)
            deleted_ipRanges = _get_deleted_obj(
                ip_range_id_list, ipaddress_range_existing, epoch_time)
            for deleted_ip in deleted_ipAddress:
                subnet.add_usedIpAddresses(deleted_ip)
            for deleted_ipRange in deleted_ipRanges:
                subnet.add_ipAddressRanges(deleted_ipRange)
        else:
            subnet.set_createEpoch(epoch_time)
            for ipaddr in subnet.get_usedIpAddresses():
                ipaddr.set_createEpoch(epoch_time)
            for ipadd_r in subnet.get_ipAddressRanges():
                ipadd_r.set_createEpoch(epoch_time)

        __save_and_expunge(session, subnet)
    except Exception:
        LOG.exception(_('error while adding/updating  Subnet'))
        raise
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def subnet_get_by_ids(context, ids):
    """This API will return a list of subnet objects which corresponds to ids

        Parameters:
            ids - List of subnet ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        subnets = session.query(Subnet).filter(
            and_(Subnet.id.in_(ids),
                 or_(Subnet.deleted == False,
                     Subnet.deleted == None))).\
            options(joinedload_all('groupIdTypes.networkType')).\
            options(joinedload('resourceTags')).\
            options(joinedload_all('ipAddressRanges.startAddress')).\
            options(joinedload_all('ipAddressRanges.endAddress')).\
            options(joinedload('usedIpAddresses')).\
            options(joinedload('parents')).\
            options(joinedload('networkSrc')).\
            options(joinedload('dnsServer')).\
            options(joinedload('dnsSuffixes')).\
            options(joinedload('defaultGateway')).\
            options(joinedload('winsServer')).\
            options(joinedload('ntpDateServer')).\
            options(joinedload('deploymentService')).\
            options(joinedload('childs')).\
            options(joinedload('redundancyPeer')).all()
        return subnets
    except Exception:
        LOG.exception(_('error while obtaining Subnets'))
        raise
    finally:
        __cleanup_session(session)


@context_api.require_admin_context
def subnet_get_all(context):
    """This API will return a list of all the Subnet objects present in DB
    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """
    session = None
    try:
        session = nova_session.get_session()
        subnets = session.query(Subnet).filter(
            or_(Subnet.deleted == False,
                Subnet.deleted == None)).\
            options(joinedload_all('groupIdTypes.networkType')).\
            options(joinedload('resourceTags')).\
            options(joinedload_all('ipAddressRanges.startAddress')).\
            options(joinedload_all('ipAddressRanges.endAddress')).\
            options(joinedload('usedIpAddresses')).\
            options(joinedload('parents')).\
            options(joinedload('networkSrc')).\
            options(joinedload('dnsServer')).\
            options(joinedload('dnsSuffixes')).\
            options(joinedload('defaultGateway')).\
            options(joinedload('winsServer')).\
            options(joinedload('ntpDateServer')).\
            options(joinedload('deploymentService')).\
            options(joinedload('childs')).\
            options(joinedload('redundancyPeer')).all()
        return subnets
    except Exception:
        LOG.exception(_('error while obtaining Subnets'))
        raise
    finally:
        __cleanup_session(session)


def __delete_vSwitch_subnet_association(session, subnetId):
    vSwitches = session.query(
        VirtualSwitch, VirtualSwitchSubnetIds).filter(
            and_(VirtualSwitchSubnetIds.subnetId == subnetId,
                 or_(VirtualSwitch.deleted == False,
                     VirtualSwitch.deleted == None))).\
        options(joinedload_all('subnets')).all()
    if len(vSwitches) > 0:
        subnetList = []
        for vSwitchType in vSwitches:
            vSwitch = vSwitchType[0]
            subnets = vSwitch.get_subnetIds()
            for subnet in subnets:
                if not subnet == subnetId:
                    subnetList.append(subnet)
            vSwitch.set_subnetIds([])
            __save_and_expunge(session, vSwitch)
            if len(subnetList) > 0:
                vSwitch.set_subnetIds(subnetList)
            __save_and_expunge(session, vSwitch)


@context_api.require_admin_context
def subnet_delete_by_ids(context, ids):
    """This API will delete Subnets objects which corresponds to ids
        Parameters:
            ids - List of subnets ids
            context - nova.context.RequestContext object (optional parameter)

    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        subnets = subnet_get_by_ids(context, ids)
        epoch_time = get_current_epoch_ms()
        for subnet in subnets:
            __delete_vSwitch_subnet_association(session, subnet.id)
            subnet.set_deletedEpoch(epoch_time)
            subnet.set_deleted(True)
            usedIpAddresses = subnet.get_usedIpAddresses()
            for usedIp in usedIpAddresses:
                usedIp.set_deletedEpoch(epoch_time)
                usedIp.set_deleted(True)
            for ip_range in subnet.get_ipAddressRanges():
                ip_range.set_deletedEpoch(epoch_time)
                ip_range.set_deleted(True)
            __save_and_expunge(session, subnet)
    except Exception:
        LOG.exception(_('error while obtaining Subnet'))
        raise
    finally:
        __cleanup_session(session)


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
    session = None
    try:
        session = nova_session.get_session()
        filtered_query = _create_filtered_ordered_query(session,
                                                        Subnet,
                                                        filters=filters,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)
        subnets = filtered_query.\
            options(joinedload_all('groupIdTypes.networkType')).\
            options(joinedload('resourceTags')).\
            options(joinedload_all('ipAddressRanges.startAddress')).\
            options(joinedload_all('ipAddressRanges.endAddress')).\
            options(joinedload('usedIpAddresses')).\
            options(joinedload('parents')).\
            options(joinedload('networkSrc')).\
            options(joinedload('dnsServer')).\
            options(joinedload('dnsSuffixes')).\
            options(joinedload('defaultGateway')).\
            options(joinedload('winsServer')).\
            options(joinedload('ntpDateServer')).\
            options(joinedload('deploymentService')).\
            options(joinedload('childs')).\
            options(joinedload('redundancyPeer')).all()
        return subnets
    except Exception:
        LOG.exception(_('Error while obtaining Subnets'))
        raise
    finally:
        __cleanup_session(session)
