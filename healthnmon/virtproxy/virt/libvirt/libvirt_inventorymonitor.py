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

'''
Created on Feb 13, 2012

@author: root
'''

from healthnmon.db import api
from healthnmon import utils as hnm_utils
from nova import db
from healthnmon.resourcemodel.healthnmonResourceModel import HostMountPoint, \
    IpProfile, OsProfile, StorageVolume, Vm, VmDisk, VmHost, \
    VmNetAdapter, VmScsiController, Property, VmGenericDevice, \
    VmGlobalSettings, VirtualSwitch, Subnet, IpAddressRange, IpAddress, \
    PortGroup
from healthnmon.constants import Constants
from healthnmon.virtproxy.events import api as event_api
from healthnmon.virtproxy.events import event_metadata
from healthnmon.virtproxy.events import util as events_util
from healthnmon.virtproxy.inventory_cache_manager import InventoryCacheManager
from healthnmon import log
from nova.context import get_admin_context
import copy
import re
import traceback
from healthnmon.utils import getFlagByKey
from healthnmon.utils import XMLUtils
from healthnmon.virtproxy.virt.libvirt.libvirt_event_monitor \
    import LibvirtEvents

LOG = log.getLogger(__name__)

libvirt = None

incomplete_vms = {}  # {compute_id : {vm_id : retry_count}}


class LibvirtInventoryMonitor:

    def __init__(self):
        global libvirt
        if libvirt is None:
            libvirt = __import__('libvirt')
        self.libvirtEvents = LibvirtEvents()

    def collectInventory(self, conn, compute_id):
        '''Handles the Host Updates '''

        LOG.info(_('Entering collectInventory for host uuid '
                   + compute_id))
        libvirtVmHost = LibvirtVmHost(conn, compute_id, self.libvirtEvents)
        libvirtVmHost.processUpdates()
        if libvirtVmHost.libvirtconn is not None:
            # Only if connection to host is available, inventory will be
            # collected for other entities
            self.hostUUID = libvirtVmHost.uuid
            if self.hostUUID is not None:
                # libvirtVmHost.processUpdates()
                LOG.info(_('***************Handling updates of Storage ' +
                           'volumes on host ' +
                           self.hostUUID + '*****************'))

                libvirtStoragePool = \
                    LibvirtStorageVolume(conn, compute_id)
                libvirtStoragePool.processUpdates()

                LOG.info(_('***************Handling updates of Networks ' +
                           'on host ' +
                           self.hostUUID + '*****************'))

                libvirtNetwork = LibvirtNetwork(conn, compute_id)
                libvirtNetwork.processUpdates()

                if self.libvirtEvents.first_poll:
                    LOG.info(_('***************Handling updates of Vms ' +
                               'on host for the first poll ' +
                               self.hostUUID + '*****************'))
                    libvirtVm = LibvirtVM(conn, compute_id)
                    libvirtVm.processUpdates()
                    self.libvirtEvents.first_poll = False
                else:
                    LOG.info(_('***************Handling updates of incomplete \
                    Vms on host '
                               + self.hostUUID + '*****************'))
                    libvirtVm = LibvirtVM(conn, compute_id)
                    libvirtVm.process_incomplete_vms()
        LOG.info(_('Exiting collectInventory for host uuid '
                   + compute_id))


class LibvirtVmHost:

    def __init__(
        self,
        connection,
        compute_id,
        libvirtEvents
    ):
        self.utils = XMLUtils()
        self.compute_id = compute_id
        self.libvirtEvents = libvirtEvents
        self.uuid = None
        self.vmHost = None
        try:
            self.rmContext = InventoryCacheManager.get_compute_inventory(
                compute_id).compute_rmcontext
            self.libvirtconn = connection
            self.uuid = self.getUuid()
        except Exception:
            LOG.error(_(' Exception while initializing LibvirtVMHost '))
            LOG.error(_(traceback.format_exc()))

    def _get_compute_running_status(self):
        compute_alive = False
        hostname = None
        computes = db.compute_node_get_all(get_admin_context())
        for compute in computes:
            computeId = str(compute['id'])
            if computeId == self.compute_id:
                service = compute['service']
                if service is not None:
                    hostname = service['host']
                    compute_alive = hnm_utils.is_service_alive(
                        service['updated_at'], service['created_at'])
        return compute_alive, hostname

    def _get_network_running_status(self, hostname):
        network_alive = False
        network_service = db.service_get_by_host_and_topic(
            get_admin_context(), hostname, 'network')
        if network_service is not None:
            network_alive = hnm_utils.is_service_alive(network_service[
                                                       'updated_at'],
                                                       network_service[
                                                       'created_at'])
        return network_alive

    """This method will set the host as disconnected
    """
    def _set_host_as_disconnected(self):
        try:
            LOG.debug(_('Entering _set_host_as_disconnected for ' +
                        'compute id: %s') % self.compute_id)
            if self.cachedvmHost.get_connectionState() == \
                    Constants.VMHOST_CONNECTED:
                self.cachedvmHost.set_connectionState(
                    Constants.VMHOST_DISCONNECTED)
                InventoryCacheManager.update_object_in_cache(
                    self.compute_id, self.cachedvmHost)
                api.vm_host_save(get_admin_context(), self.cachedvmHost)
                LOG.audit(_('Host with (UUID, host name) - (%s, %s) got ' +
                            'disconnected') % (self.compute_id,
                                               self.cachedvmHost.get_name()))
                event_api.notify_host_update(
                    event_metadata.EVENT_TYPE_HOST_UPDATED, self.cachedvmHost)
                event_api.notify_host_update(
                    event_metadata.EVENT_TYPE_HOST_DISCONNECTED,
                    self.cachedvmHost)
            LOG.info(_(' The compute id %s is in the disconnected state')
                     % self.compute_id)
        except Exception:
            LOG.error(_(' Exception while setting the compute to ' +
                        'disconnected state. id  %s') % self.compute_id)
            LOG.error(_(traceback.format_exc()))

    def processUpdates(self):
        LOG.debug(_('Entering processUpdates for host uuid '
                  + self.compute_id))
        try:
            self.cachedvmHost = \
                InventoryCacheManager.get_object_from_cache(
                    self.compute_id,
                    Constants.VmHost)

            """Check whether the compute is running else exit from polling"""
            compute_alive, hostname = self._get_compute_running_status()
            network_alive = self._get_network_running_status(hostname)
            if not compute_alive or not network_alive:
                if self.cachedvmHost is not None:
                    LOG.debug(_('De-registering the host with compute_id %s \
                    for events ' % str(
                        self.compute_id)))
                    self.libvirtEvents.deregister_libvirt_events()
                    self._set_host_as_disconnected()
                    self.libvirtconn = None
                    return
            if not self.libvirtEvents.registered:
                LOG.debug(_('Registering host with ' +
                            'compute_id %s for events ' %
                            str(self.compute_id)))
                self.libvirtEvents.compute_id = self.compute_id
                self.libvirtEvents.register_libvirt_events()
                self.libvirtEvents.first_poll = True
            # Below are the scenarios in which the cachedvmHost would be None
            # 1. SSH not setup before attempting to collect
            #    inventory for the first time
            # 2. SSH setup, but libvirt service is down, before attempting
            #    to collect inventory for the first time
            # If inventory has been collected atleast once,cachedvmHost
            # will not be None and the host connection state will
            # be updated as disconnected
            if (self.libvirtconn is None and self.cachedvmHost is None):
                return

            self.vmHost = VmHost()

            # Map the libvirt object to VmHost object
            self._mapHostProperties()

            if self.cachedvmHost is not None:
                self.vmHost.set_virtualMachineIds(
                    self.cachedvmHost.get_virtualMachineIds())
                self.vmHost.set_storageVolumeIds(
                    self.cachedvmHost.get_storageVolumeIds())
                self.vmHost.set_virtualSwitches(
                    self.cachedvmHost.get_virtualSwitches())
                self.vmHost.set_portGroups(self.cachedvmHost.get_portGroups())
                self.vmHost.set_ipAddresses(
                    self.cachedvmHost.get_ipAddresses())

            if self.utils.getdiff(self.cachedvmHost, self.vmHost)[0]:
                # Perist the Vm in cache and in DB
                InventoryCacheManager.update_object_in_cache(self.compute_id,
                                                             self.vmHost)
                InventoryCacheManager.get_compute_inventory(
                    self.compute_id).update_compute_info(self.rmContext,
                                                         self.vmHost)
                self._persist()
                if self.cachedvmHost is not None:
                    cachedHoststate = \
                        self.cachedvmHost.get_connectionState()
                    currentHostState = self.vmHost.get_connectionState()
                    if cachedHoststate != currentHostState:
                        if currentHostState == Constants.VMHOST_CONNECTED:
                            LOG.audit(_('Host with (UUID, host name) - ' +
                                        '(%s, %s) got connected') %
                                      (self.uuid, self.vmHost.get_name()))
                            event_api.notify_host_update(
                                event_metadata.EVENT_TYPE_HOST_CONNECTED,
                                self.vmHost)
                            event_api.notify_host_update(
                                event_metadata.EVENT_TYPE_HOST_UPDATED,
                                self.vmHost)
                        elif currentHostState \
                                == Constants.VMHOST_DISCONNECTED:
                            LOG.audit(_('Host with (UUID, host name) - ' +
                                        '(%s, %s) got disconnected') %
                                      (self.uuid, self.vmHost.get_name()))
                            event_api.notify_host_update(
                                event_metadata.EVENT_TYPE_HOST_DISCONNECTED,
                                self.vmHost)
                            event_api.notify_host_update(
                                event_metadata.EVENT_TYPE_HOST_UPDATED,
                                self.vmHost)
                            LOG.debug(_('Un-registering the host for events'))
                            self.libvirtEvents.deregister_libvirt_events()
                else:
                    # Generate Host Added Event
                    LOG.audit(_('Host with (UUID, host name) - ' +
                                '(%s, %s) got added') %
                              (self.uuid, self.vmHost.get_name()))
                    event_api.notify_host_update(
                        event_metadata.EVENT_TYPE_HOST_ADDED,
                        self.vmHost)
        except Exception:
            LOG.error(_('Could not proceed with process updates of ' +
                        'VmHost with id ' + self.compute_id))
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting processUpdates for host uuid '
                  + self.compute_id))

    def _mapHostProperties(self):
        ''' Implement the mapping of properties '''

        LOG.debug(_('Entering _mapHostProperties for host uuid '
                  + self.compute_id))
        if self.libvirtconn is not None:
            self.vmHost.set_connectionState(Constants.VMHOST_CONNECTED)
            hostCapXml = self.libvirtconn.getCapabilities()
            hostSysXml = self.libvirtconn.getSysinfo(0)

            self._mapHostCapabilitiesInfo(hostCapXml)
            self._mapHostSystemInfo(hostSysXml)
            self._mapHostOsInfo()
            self._mapHostInfo()
        else:
            if self.cachedvmHost is not None:
                self.vmHost = copy.deepcopy(self.cachedvmHost)
            self.vmHost.set_connectionState(Constants.VMHOST_DISCONNECTED)

        LOG.debug(_('Exiting _mapHostProperties for host uuid '
                  + self.compute_id))

    def _mapHostCapabilitiesInfo(self, hostCapXml):
        LOG.debug(_('Entering _mapHostCapabilitiesInfo for host uuid '
                  + self.compute_id))
        self.uuid = self.utils.parseXML(hostCapXml, '//host/uuid')
        self.vmHost.set_uuid(self.uuid)
        self.vmHost.set_id(self.compute_id)
        self.vmHost.set_resourceManagerId(self.uuid)

        cpuarch = self.utils.parseXML(hostCapXml, '//host/cpu/arch')
        self.vmHost.set_processorArchitecture(cpuarch.upper())

        LOG.debug(_('Exiting _mapHostCapabilitiesInfo for host uuid '
                  + self.compute_id))

    def _mapHostSystemInfo(self, hostSysXml):
        LOG.debug(_('Entering _mapHostSystemInfo for host uuid '
                  + self.compute_id))
        model = self.utils.parseXML(hostSysXml, '//system/entry')[1]
        if model:
            self.vmHost.set_model(model.strip())

        serialNumber = self.utils.parseXML(hostSysXml, '//system/entry')[3]
        if serialNumber:
            self.vmHost.set_serialNumber(serialNumber.strip())
        LOG.debug(_('Exiting _mapHostSystemInfo for host uuid '
                  + self.compute_id))

    def _mapHostOsInfo(self):
        LOG.debug(_('Entering _mapHostOsInfo for host uuid '
                  + self.compute_id))
        os = self.vmHost.get_os()
        if os is None:
            os = OsProfile()
        os.set_resourceId(self.vmHost.get_id())
        os.set_osName(self.libvirtconn.getType())
        os.set_osVersion(self.libvirtconn.getVersion())
        os.set_osType('KVM')
        os.set_osDescription('KVM')
        self.vmHost.set_os(os)
        LOG.debug(_('Exiting _mapHostOsInfo for host uuid '
                  + self.compute_id))

    def _mapHostInfo(self):
        LOG.debug(_('Entering _mapHostInfo for host uuid '
                  + self.compute_id))
        self.vmHost.set_virtualizationType('QEMU')
        (totalMemory, memoryConsumed) = self.get_memory_info()
        self.vmHost.set_memorySize(totalMemory)
        self.vmHost.set_name(self.libvirtconn.getHostname())
        self.vmHost.set_memoryConsumed(memoryConsumed)
        self.vmHost.set_processorCount(
            self.libvirtconn.getInfo()[5] * self.libvirtconn.getInfo()[7])
        self.vmHost.set_processorCoresCount(self.libvirtconn.getInfo()[2])
        self.vmHost.set_processorSpeedMhz(self.libvirtconn.getInfo()[3])
        self.vmHost.set_processorSpeedTotalMhz(
            self.libvirtconn.getInfo()[3] *
            self.vmHost.get_processorCoresCount())
        self.vmHost.set_hyperThreadEnabled(False)
        if (self.libvirtconn.getInfo()[7] > 1):
            self.vmHost.set_hyperThreadEnabled(True)
        LOG.debug(_('Exiting _mapHostInfo for host uuid '
                  + self.compute_id))

    def get_memory_info(self):
        global libvirt
        totalMemory = 0
        memoryConsumed = 0
        try:
            memstats = self.libvirtconn.getMemoryStats(
                libvirt.VIR_NODE_MEMORY_STATS_ALL_CELLS, 0)
            totalMemory = memstats['total']
            freeMemory = memstats['free'] + memstats[
                'buffers'] + memstats['cached']
            memoryConsumed = totalMemory - freeMemory
        except Exception, err:
            LOG.error(_("Error reading memory stats for host %s: %s"
                        % (self.uuid, err)))
        return (totalMemory, memoryConsumed)

    def getUuid(self):
        if self.uuid is None and self.libvirtconn is not None:
            hostCapXml = self.libvirtconn.getCapabilities()
            self.uuid = self.utils.parseXML(hostCapXml, '//host/uuid')
        return self.uuid

    def _persist(self):
        LOG.debug(_('Entering _persist for host uuid '
                  + self.compute_id))
        api.vm_host_save(get_admin_context(), self.vmHost)
        LOG.debug(_('Exiting _persist for host uuid '
                  + self.compute_id))


class LibvirtVM:

    def __init__(self,
                 connection,
                 compute_id
                 ):
        self.libvirtconn = connection
        self.Vm = None
        self.domainObj = None
        self.domainUuid = None
        self.utils = XMLUtils()
        self.compute_id = compute_id
        self.cachedVm = None
        self.vmHost = \
            InventoryCacheManager.get_object_from_cache(
                self.compute_id,
                Constants.VmHost)
        self.hostUUID = self.vmHost.uuid
        self.vmAdded = False
        self.vmDeleted = False

    def processUpdates(self):
        ''' Method will iterate through the domainList and get
        the mapping done for Resource Model "Vm" '''

        LOG.debug(_('Entering processUpdates for vms on host '
                  + self.compute_id))
        try:
            inactivedomainList = self.libvirtconn.listDefinedDomains()
            activeDomainList = self.libvirtconn.listDomainsID()

    #        domainList = self.libvirtconn.listDefinedDomains()
            vmIds = self.vmHost.get_virtualMachineIds()
            updatedVmIds = []

            for dom in inactivedomainList:
                domainObj = self.libvirtconn.lookupByName(dom)
                self._processVm(domainObj)
                updatedVmIds.append(domainObj.UUIDString())

            for dom in activeDomainList:
                domainObj = self.libvirtconn.lookupByID(dom)
                self._processVm(domainObj)
                updatedVmIds.append(domainObj.UUIDString())

            self.vmHost.set_virtualMachineIds(updatedVmIds)
            InventoryCacheManager.update_object_in_cache(
                self.compute_id,
                self.vmHost)
            self.processVmDeletes(vmIds, updatedVmIds)
            if (self.vmAdded or self.vmDeleted):
                event_api.notify_host_update(
                    event_metadata.EVENT_TYPE_HOST_UPDATED, self.vmHost)
        except Exception:
            LOG.error(_('Could not proceed with process updates of \
                Vm on host with id ' + self.compute_id))
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting processUpdates for vms on host '
                  + self.compute_id))

    def get_existing_domain_uuids(self):
        existingVmIds = []
        inactivedomainList = self.libvirtconn.listDefinedDomains()
        activeDomainList = self.libvirtconn.listDomainsID()
        for dom in inactivedomainList:
            inactive_domainObj = self.libvirtconn.lookupByName(dom)
            existingVmIds.append(inactive_domainObj.UUIDString())
        for dom in activeDomainList:
            active_domainObj = self.libvirtconn.lookupByID(dom)
            existingVmIds.append(active_domainObj.UUIDString())
        LOG.debug(_('Existing vm ids %s'), existingVmIds)
        return existingVmIds

    def process_incomplete_vms(self):
        """ Process incomplete vms on a host """
        global incomplete_vms
        if self.compute_id in incomplete_vms:
            vm_dic = incomplete_vms[self.compute_id]
            if vm_dic:
                LOG.debug(_('Processing VMs %s'), vm_dic)
                existingVmIds = self.get_existing_domain_uuids()
                for vm_id in vm_dic.keys():
                    if vm_id in existingVmIds:
                        domainObj = self.libvirtconn.lookupByUUIDString(vm_id)
                        self._processVm(domainObj)
                    else:
                        # Vm got deleted. Remove it from incomplete list
                        del vm_dic[vm_id]

    def process_updates_for_updated_VM(self, domainObj_notified):
        ''' Method will process the domainobj and get the mapping done
        for Resource Model "Vm" '''
        try:
            LOG.info(_('Processing updates for VM %s reported \
            by libvirt event' % domainObj_notified.UUIDString()))
            vmIds = self.vmHost.get_virtualMachineIds()
            existingVmIds = self.get_existing_domain_uuids()
            if domainObj_notified.UUIDString() in existingVmIds:
                self._processVm(domainObj_notified)
                self.vmHost.set_virtualMachineIds(existingVmIds)
                InventoryCacheManager.update_object_in_cache(
                    self.compute_id,
                    self.vmHost)
            else:
                self.vmHost.set_virtualMachineIds(existingVmIds)
                InventoryCacheManager.update_object_in_cache(
                    self.compute_id,
                    self.vmHost)
                self.processVmDeletes(vmIds, existingVmIds)

            if (self.vmAdded or self.vmDeleted):
                event_api.notify_host_update(
                    event_metadata.EVENT_TYPE_HOST_UPDATED, self.vmHost)
        except Exception:
            LOG.error(_('Could not proceed with process updates of Vm\
            on host with id ' + self.compute_id))
            self.utils = XMLUtils()
            self.utils.log_error(traceback.format_exc())
        LOG.info(_('Exiting processUpdates for vms on host ' +
                   self.compute_id))

    def _processVm(self, domainObj):
        ''' Method to map the domain object to the Vm Object '''
        try:
            LOG.debug(_('Entering _processVm for vm '
                      + domainObj.UUIDString() + ' on host '
                      + self.compute_id))
            self.domainObj = domainObj
            self.domainUuid = self.domainObj.UUIDString()

            self.cachedVm = \
                InventoryCacheManager.get_object_from_cache(
                    self.domainUuid,
                    Constants.Vm)
            self.Vm = Vm()

            # if(self.domainObj.isUpdated is True):
            # Sets the values into the self.Vm
            self._mapVmProperties()
            # Now compare the VmObject with the new Vm created
            # Assuming that if both the objects are same compare()
            # will return true, else false
            diff_res_tup = self.utils.getdiff(self.cachedVm, self.Vm)
            if diff_res_tup[0]:
                '''if cachedVm !=None:
                    print "CachedVm :",cachedVm.__dict__
                if self.Vm !=None:
                    print "self.Vm :",self.Vm.__dict__'''
                # Persist the Vm in cache and in DB
                InventoryCacheManager.update_object_in_cache(
                    self.domainUuid,
                    self.Vm)
                self._persistVm()
                # Generates the Event when Vm is added, Vm reconfigured
                # mand if Vm state changes
                if self.cachedVm is None:
                    LOG.audit(_('New Vm '
                              + domainObj.UUIDString() + ' created on host '
                              + self.compute_id))
                    event_api.notify(event_metadata.EVENT_TYPE_VM_CREATED,
                                     self.Vm)
                    self.vmAdded = True
                else:
                    currentVmState = self.Vm.get_powerState()
                    cachedVmState = self.cachedVm.get_powerState()
                    if currentVmState != cachedVmState:
                        if currentVmState \
                                == Constants.VM_POWER_STATES[1]:
                            if cachedVmState \
                                    == Constants.VM_POWER_STATES[3]:
                                LOG.audit(_('Vm '
                                            + domainObj.UUIDString()
                                            + ' is resumed on host '
                                            + self.compute_id))
                                event_api.notify(
                                    event_metadata.EVENT_TYPE_VM_RESUMED,
                                    self.Vm)
                            else:
                                LOG.audit(_('Vm '
                                            + domainObj.UUIDString()
                                            + ' is started on host '
                                            + self.compute_id))
                                event_api.notify(
                                    event_metadata.EVENT_TYPE_VM_STARTED,
                                    self.Vm)
                        elif currentVmState \
                                == Constants.VM_POWER_STATES[3]:
                            LOG.audit(_('Vm '
                                        + domainObj.UUIDString()
                                        + ' is suspended on host '
                                        + self.compute_id))
                            event_api.notify(
                                event_metadata.EVENT_TYPE_VM_SUSPENDED,
                                self.Vm)
                        elif currentVmState \
                                == Constants.VM_POWER_STATES[5]:
                            LOG.audit(_('Vm '
                                        + domainObj.UUIDString()
                                        + ' is stopped on host '
                                        + self.compute_id))
                            event_api.notify(
                                event_metadata.EVENT_TYPE_VM_STOPPED,
                                self.Vm)
                        elif currentVmState \
                                == Constants.VM_POWER_STATES[4]:
                            LOG.audit(_('Vm '
                                        + domainObj.UUIDString()
                                        + ' is shutdown on host '
                                        + self.compute_id))
                            event_api.notify(
                                event_metadata.EVENT_TYPE_VM_SHUTDOWN,
                                self.Vm)

                    # Vm Reconfigured events

                    changed_attr = \
                        events_util.getChangedAttributesForUpdateEvent(
                            self.Vm,
                            diff_res_tup[1])
                    if changed_attr is not None and len(changed_attr) > 0:
                        LOG.audit(_('Vm '
                                    + domainObj.UUIDString()
                                    + ' is reconfigured on host '
                                    + self.compute_id))
                        event_api.notify(
                            event_metadata.EVENT_TYPE_VM_RECONFIGURED,
                            self.Vm,
                            changed_attributes=changed_attr)
            LOG.debug(_('Exiting _processVm for vm '
                        + domainObj.UUIDString() + ' on host '
                        + self.compute_id))
        except Exception:
            self.utils.log_error(traceback.format_exc())

    def _mapVmProperties(self):
        ''' Implement the mapping of properties '''

        try:
            LOG.debug(_('Entering _mapVmProperties for vm '
                      + self.domainUuid + ' on host '
                      + self.compute_id))
            self.Vm.set_id(self.domainUuid)
            self.Vm.set_resourceManagerId(self.hostUUID)
            self.Vm.set_vmHostId(self.compute_id)
            self.Vm.set_virtualizationType('QEMU')
            try:
                self.vm_info = db.instance_get_by_uuid(get_admin_context(),
                                                       self.domainUuid)
                self.Vm.set_name(str(self.vm_info['display_name']))
            except Exception:
                self.Vm.set_name(self.domainObj.name())
                LOG.error(_('Instance %s does not exist in nova') %
                          self.domainUuid)

            vmXML = self.domainObj.XMLDesc(0)

            # Call the mapper methods to pass the Vm Xml and set in self.Vm
            self._mapGenericVmInfo(vmXML)
            self._mapVmDisk(vmXML)
            self._mapVmNetAdapter(vmXML)
            self._mapScsiController(vmXML)
            self._mapOsProfile(vmXML)
            self._mapPowerState()
            self._mapConnectionState()
            self._mapBootOrder(vmXML)
            self._mapGenericDevices(vmXML)
            self._mapGlobalSettings()
            LOG.debug(_('Exiting _mapVmProperties for vm '
                      + self.domainUuid + ' on host '
                      + self.compute_id))
        except Exception:
            self.utils.log_error(traceback.format_exc())

    def _mapGenericVmInfo(self, vmXML):
        LOG.debug(_('Entering _mapGenericVmInfo for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))
        memorySize = self.utils.parseXML(vmXML, "//domain/memory")
        if (memorySize is not None):
            self.Vm.set_memorySize(long(memorySize))
        memoryConsumed = self.utils.parseXML(vmXML, "//domain/currentMemory")
        if (memoryConsumed is not None):
            self.Vm.set_memoryConsumed(long(memoryConsumed))
        hostInfo = self.libvirtconn.getInfo()
        self.Vm.set_processorArchitecture(hostInfo[0].upper())
        self.Vm.set_processorSpeedMhz(hostInfo[3])
        processorCores = self.utils.parseXMLAttributes(
            vmXML,
            "//domain/cpu/topology", "cores")
        if (processorCores is not None):
            self.Vm.set_processorCoresCount(int(processorCores))
        processorCount = self.utils.parseXML(vmXML, "//domain/vcpu")
        if (processorCount is not None):
            self.Vm.set_processorCount(int(processorCount))
        if hostInfo[3] is not None and processorCores is not None:
            processorSpeedTotalMhz = int(hostInfo[3]) \
                * int(processorCores)
            self.Vm.set_processorSpeedTotalMhz(processorSpeedTotalMhz)
        self.Vm.set_serialNumber(self.domainUuid)
        LOG.debug(_('Exiting _mapGenericVmInfo for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))

    def _mapVmDisk(self, vmXML):
        '''Mapper Method to handle the VmDisk Object '''

        LOG.debug(_('Entering _mapVmDisk for vm ' + self.domainUuid
                  + ' on host ' + self.compute_id))
        disksAttached = self.utils.getNodeXML(
            vmXML,
            "//domain/devices/disk[@device='disk']")
        vmDiskList = []
        for disk in disksAttached:
            vmDisk = VmDisk()
            diskXmlStr = str(disk)
            if self.utils.parseXMLAttributes(
                    diskXmlStr, '//disk/source', 'file') is not None:
                filePath = self.utils.parseXMLAttributes(
                    diskXmlStr, '//disk/source', 'file')
            elif self.utils.parseXMLAttributes(
                    diskXmlStr,
                    '//disk/source', 'dev') is not None:
                filePath = self.utils.parseXMLAttributes(
                    diskXmlStr,
                    '//disk/source', 'dev')
            vmDisk.set_fileName(filePath)
            vmDisk.set_id(filePath)
            channel = self.utils.parseXMLAttributes(
                diskXmlStr, "//disk/address", "unit")
            if (channel is not None):
                vmDisk.set_channel(int(channel))
            controllerId = self.utils.parseXMLAttributes(
                diskXmlStr, "//disk/address", "controller")
            if (controllerId is not None):
                vmDisk.set_controllerId(int(controllerId))
            vmDisk.set_controllerType(
                self.utils.parseXMLAttributes(diskXmlStr,
                                              '//disk/target', 'bus'))
            vmDisk.set_mode(None)
            storageVolPath = filePath
            try:
                diskSize = self.domainObj.blockInfo(storageVolPath, 0)[0]
                vmDisk.set_diskSize(diskSize)
                fileSize = self.domainObj.blockInfo(storageVolPath, 0)[1]
                vmDisk.set_fileSize(fileSize)
                poolUUID = None
                storagePoolsPaths = self._getStoragePoolPath()
                storageVolPath = \
                    self._getStorageVolumePath(storagePoolsPaths,
                                               storageVolPath)
                if storageVolPath is not None:
                    storageVol = None
                    try:
                        storageVol = self._get_instance_disk(storageVolPath)
                    except Exception:
                        self.utils.log_error(traceback.format_exc())
                    if storageVol is None:
                        # Disk not yet attached.
                        # Add vm to incomplete list for retry
                        global incomplete_vms
                        if self.compute_id in incomplete_vms:
                            if self.domainUuid in \
                                    incomplete_vms[self.compute_id]:
                                retry_count = incomplete_vms[
                                    self.compute_id][self.domainUuid]
                            else:
                                retry_count = 0
                        else:
                            incomplete_vms[self.compute_id] = {}
                            retry_count = 0
                        if retry_count < 5:
                            LOG.debug(_(
                                "Instance disk not yet created. \
                                Will be retried during next poll"))
                            retry_count += 1
                            incomplete_vms[self.compute_id][
                                self.domainUuid] = retry_count
                        else:
                            LOG.error(_(
                                "Instance disk does not exist or not\
                                 yet created. Maximum retries reached."))
                        continue
                    else:
                        # Disk inventory complete.
                        # Remove this vm from incomplete list
                        if self.compute_id in incomplete_vms and \
                                self.domainUuid in \
                                incomplete_vms[self.compute_id]:
                            del incomplete_vms[
                                self.compute_id][self.domainUuid]
                    LOG.debug(_("Storage Volume : %s"), storageVol)
                    poolObj = storageVol.storagePoolLookupByVolume()
                    poolUUID = poolObj.UUIDString()
                    vmDisk.set_storageVolumeId(poolUUID)
                    vmDiskList.append(vmDisk)
                else:
                    LOG.debug(_('There is no storage pool present for this \
                    storage volume ' + self.domainUuid
                                + ' on host ' + self.compute_id))

            except Exception:
                self.utils.log_error(traceback.format_exc())

        self.Vm.set_vmDisks(vmDiskList)
        LOG.debug(_('Exiting _mapVmDisk for vm ' + self.domainUuid
                  + ' on host ' + self.compute_id))

    """Method to lookup for instance storage volume."""
    def _get_instance_disk(self, storage_vol_path):
        storageVol = self.libvirtconn.storageVolLookupByPath(storage_vol_path)
        return storageVol

    def _getStoragePoolPath(self):
        ''' if this is a openstack volume (check /var/lib/nova )
            then remove the disk from path
            if /var/lib/nova/instances/instance-00000004/disk is path
            then new path will be
                /var/lib/nova/instances/instance-00000004 '''

        LOG.debug(_('Entering _getStoragePoolPath for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))
        storagePools = self.libvirtconn.listStoragePools()
        storagePoolsPath = []
        for pool in storagePools:
            storage = self.libvirtconn.storagePoolLookupByName(pool)
            poolXML = str(storage.XMLDesc(0))
            path = self.utils.parseXML(poolXML, '//pool/target/path')
            storagePoolsPath.append(path)
        LOG.debug(_('Exiting _getStoragePoolPath for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))
        return storagePoolsPath

    def _getStorageVolumePath(self, storagePoolsPaths, storageVolPath):
        LOG.debug(_('Entering _getStorageVolumePath for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))
        while storageVolPath.rfind('/') != -1:
            storageVolPath_old = storageVolPath
            regexOutput = re.search('^(.*/)', storageVolPath)
            storageVolPath = regexOutput.group(0)
            storageVolPath = storageVolPath.rstrip('/')
            if storageVolPath in storagePoolsPaths:
                LOG.debug(_('Exiting _getStorageVolumePath for vm '
                          + self.domainUuid + ' on host '
                          + self.compute_id))
                return storageVolPath_old
        LOG.debug(_('Exiting _getStorageVolumePath for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))
        return None

    def _mapVmNetAdapter(self, vmXML):
        '''Mapper method to handle the VmNetAdapter Object '''

        LOG.debug(_('Entering _mapVmNetAdapter for vm '
                    + self.domainUuid + ' on host ' + self.compute_id))
        vmNetAdapterAttached = self.utils.getNodeXML(
            vmXML,
            '//domain/devices/interface')
        vmNetAdapterList = []
        ipProfileList = []
        for netAdapter in vmNetAdapterAttached:
            vmNetAdapter = VmNetAdapter()
            interfaceXml = str(netAdapter)
            vmNetAdapter.set_adapterType(
                self.utils.parseXMLAttributes(interfaceXml,
                                              '//interface/model', 'type'))
            vmNetAdapter.set_addressType(
                self.utils.parseXMLAttributes(
                    interfaceXml,
                    '//interface/address', 'type'))
            mac_address = self.utils.parseXMLAttributes(
                interfaceXml,
                '//interface/mac', 'address')
            vmNetAdapter.set_macAddress(mac_address)
            vmNetAdapter.set_id(mac_address)
            filterrefobjs = self.utils.getNodeXML(interfaceXml,
                                                  '//interface/filterref')
            ipAddress = []
            for filterobj in filterrefobjs:
                filterrefobjxml = str(filterobj)
                ip = self.utils.parseXMLAttributes(
                    filterrefobjxml,
                    "//filterref/parameter[@name='IP']", 'value', False)
                if ip:
                    ipAddress.append(ip)
            if ipAddress:
                vmNetAdapter.set_ipAddresses(ipAddress)
                for ip in ipAddress:
                    ipProfile = self._mapIpProfile(ip)
                    if ipProfile is not None and \
                        self.utils.is_profile_in_list(
                            ipProfile, ipProfileList) is not True:
                        ipProfileList.append(ipProfile)

            vmNetAdapter.set_switchType('vSwitch')
            network_type = self.utils.parseXMLAttributes(
                interfaceXml,
                '//interface', 'type')
            networkName = None
            if network_type == 'bridge':
                networkName = \
                    self.utils.parseXMLAttributes(
                        interfaceXml,
                        '//interface/source', 'bridge')
            elif network_type == 'network':
                networkName = \
                    self.utils.parseXMLAttributes(
                        interfaceXml,
                        '//interface/source', 'network')
            vmNetAdapter.set_networkName(networkName)

            vmNetAdapterList.append(vmNetAdapter)

        self.Vm.set_vmNetAdapters(vmNetAdapterList)
        self.Vm.set_ipAddresses(ipProfileList)
        LOG.debug(_('Exiting _mapVmNetAdapter for vm '
                  + self.domainUuid + ' in host ' + self.compute_id))

    def _mapScsiController(self, vmXML):
        '''Mapper method to handle the VmScsiController Object '''

        LOG.debug(_('Entering _mapScsiController for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))
        scsiControllerAttached = self.utils.getNodeXML(
            vmXML,
            "//domain/devices/controller[@type='scsi']")
        scsiControllerList = []
        for scsiController in scsiControllerAttached:
            vmScsiController = VmScsiController()
            scsiControllerXmlStr = str(scsiController)

            controllerId = \
                self.utils.parseXMLAttributes(scsiControllerXmlStr,
                                              '//controller', 'index')
            controllerType = \
                self.utils.parseXMLAttributes(scsiControllerXmlStr,
                                              '//controller', 'type')
            controllerName = controllerType + ':' + str(controllerId)
            vmScsiController.set_id(self.domainUuid + '_'
                                    + controllerName)
            vmScsiController.set_controllerId(controllerId)
            vmScsiController.set_controllerName(controllerName)
            vmScsiController.set_type(controllerType)
            vmScsiController.set_busSharing(None)

            scsiControllerList.append(vmScsiController)

        self.Vm.set_vmScsiControllers(scsiControllerList)
        LOG.debug(_('Exiting _mapScsiController for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))

    def _mapOsProfile(self, vmXML):
        pass

    def _mapPowerState(self):
        LOG.debug(_('Entering _mapPowerState for vm ' + self.domainUuid
                  + ' on host ' + self.compute_id))
        state = None
        intstate = self.domainObj.state(0)
        if len(intstate) > 0:
            state = intstate[0]
        self.Vm.set_powerState(Constants.VM_POWER_STATES[state])
        LOG.debug(_('Exiting _mapPowerState for vm ' + self.domainUuid
                  + ' on host ' + self.compute_id))

    def _mapConnectionState(self):
        LOG.debug(_('Entering _mapConnectionState for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))
        if self.domainObj.isActive() > 0:
            value = Constants.VM_CONNECTED
        else:
            value = Constants.VM_DISCONNECTED
        self.Vm.set_connectionState(value)
        LOG.debug(_('Exiting _mapConnectionState for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))

    def _mapBootOrder(self, vmXML):
        LOG.debug(_('Entering _mapBootOrder for vm ' + self.domainUuid
                  + ' on host ' + self.compute_id))
        try:
            bootorderobject = self.utils.getNodeXML(vmXML, '//domain/os')
            bootpath = None
            for bo in bootorderobject:
                bootorderXMLStr = str(bo)
                path_list = self.utils.parseXMLAttributes(
                    bootorderXMLStr,
                    '//os/boot', 'dev', True)
                if path_list:
                    bootpath = ",".join(path_list)
            self.Vm.set_bootOrder(bootpath)
        except Exception:
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting _mapBootOrder for vm ' + self.domainUuid
                  + ' on host ' + self.compute_id))

    def _mapGenericDevices(self, vmXML):
        '''Mapper Method to handle the VmGenericDevice Object '''

        try:
            LOG.debug(_('Entering _mapGenericDevices for vm '
                      + self.domainUuid + ' on host '
                      + self.compute_id))
            deviceAttached = self.utils.getNodeXML(
                vmXML,
                "//domain/devices/disk[@device != 'disk']")
            vmDeviceList = []
            genericdevice = None
            genericdeviceList = []

            for device in deviceAttached:
                deviceXmlStr = str(device)

                if self.cachedVm is not None:
                    genericdeviceList = \
                        self.cachedVm.get_vmGenericDevices()

                if len(genericdeviceList) == 0:
                    genericdevice = VmGenericDevice()
                else:
                    for gendevice in genericdeviceList:
                        genericdevice = gendevice
                        if genericdevice.get_name() \
                            == self.utils.parseXMLAttributes(
                                deviceXmlStr,
                                '//disk', 'device'):
                            break

                genericdevice.set_name(
                    self.utils.parseXMLAttributes(
                        deviceXmlStr,
                        '//disk', 'device'))
                properties = genericdevice.get_properties()
                self._updateProperties(
                    properties, 'type', 'type',
                    self.utils.parseXMLAttributes(deviceXmlStr,
                                                  '//disk/address', 'type'))
                controller_type = self.utils.parseXMLAttributes(
                    deviceXmlStr,
                    '//disk/target', 'bus')
                self._updateProperties(properties,
                                       'controller_type',
                                       'controller_type',
                                       controller_type)
                self._updateProperties(properties,
                                       'controller',
                                       'controller',
                                       self.utils.parseXMLAttributes(
                                           deviceXmlStr,
                                           '//disk/address',
                                           'controller'))
                bus = self.utils.parseXMLAttributes(
                    deviceXmlStr,
                    '//disk/address', 'bus')
                self._updateProperties(properties, 'bus', 'bus', bus)
                unit = self.utils.parseXMLAttributes(deviceXmlStr,
                                                     '//disk/address', 'unit')
                self._updateProperties(properties, 'unit', 'unit', unit)

                genericdevice.set_id(controller_type + bus + ':' + unit)
                genericdevice.set_properties(properties)
                vmDeviceList.append(genericdevice)

            self.Vm.set_vmGenericDevices(vmDeviceList)
        except Exception:
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting _mapGenericDevices for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))

    def _mapGlobalSettings(self):
        '''Mapper Method to handle the VmGenericDevice Object '''

        try:
            LOG.debug(_('Entering _mapGlobalSettings for vm '
                      + self.domainUuid + ' on host '
                      + self.compute_id))
            vmGlobalSettings = VmGlobalSettings()
            if self.domainObj.autostart() > 0:
                value = Constants.AUTO_START_ENABLED
            else:
                value = Constants.AUTO_START_DISABLED
            vmGlobalSettings.set_autoStartAction(value)
            vmGlobalSettings.set_id(self.Vm.get_id())
            self.Vm.set_vmGlobalSettings(vmGlobalSettings)
        except Exception:
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting _mapGlobalSettings for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))

    def _updateProperties(self,
                          properties,
                          name,
                          note,
                          value,
                          ):

        LOG.debug(_('Entering _updateProperties for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))
        try:
            prop = None
            found = False
            for pty in properties:
                found = False
                if name.lower() == pty.get_name().lower():
                    prop = pty
                    found = True
                    break
            if found is True:
                prop.set_note(note)
                prop.set_value(value)
            else:
                prop = Property()
                prop.set_name(name)
                prop.set_note(note)
                prop.set_value(value)
                properties.append(prop)
        except Exception:
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting _updateProperties for vm '
                  + self.domainUuid + ' on host ' + self.compute_id))

    def _mapIpProfile(self, ipAddress):
        '''Handles the mapping of IpProfile Object '''

        LOG.debug(_('Entering _mapIpProfile for vm ' + self.domainUuid
                  + ' for IPaddress ' + ipAddress + ' on host '
                  + self.compute_id))
        ipProfile = IpProfile()
        ipProfile.set_ipAddress(ipAddress)
        ipProfile.set_hostname(self.vmHost.get_name())
        ipType = None
        if ipAddress.find('.') != -1:
            ipType = 'IPV4'
        elif ipAddress.find(':') != -1:
            ipType = 'IPV6'
        ipProfile.set_ipType(ipType)
        LOG.debug(_('Exiting _mapIpProfile for vm ' + self.domainUuid
                  + ' for IPaddress ' + ipAddress + ' on host '
                  + self.compute_id))
        return ipProfile

    def processVmDeletes(self, oldVmIds, updatedVmIds):
        LOG.debug(_('Entering processVmDeletes for host '
                  + self.compute_id))

        # Should identify vm's which have been deleted
        # Should remove the corresponding vm object from cache and DB
        # Should update the host object's vm list in both cache and DB

        deletion_list = self.utils.getDeletionList(oldVmIds, updatedVmIds)
        if len(deletion_list) != 0:
            # Delete object from cache
            vm_deleted_list = []
            for vmId in deletion_list:
                obj = InventoryCacheManager.get_object_from_cache(vmId,
                                                                  Constants.Vm)
                if obj is not None:
                    vm_deleted_list.append(obj)
                InventoryCacheManager.delete_object_in_cache(vmId,
                                                             Constants.Vm)
            api.vm_delete_by_ids(get_admin_context(), deletion_list)
            for vm_deleted in vm_deleted_list:
                LOG.audit(_('Vm '
                          + str(vm_deleted.get_id()) + ' deleted on host '
                          + self.compute_id))
                event_api.notify(event_metadata.EVENT_TYPE_VM_DELETED,
                                 vm_deleted)
                self.vmDeleted = True
        LOG.debug(_('Exiting processVmDeletes for host '
                  + self.compute_id))

    def _persistVm(self):
        LOG.debug(_('Entering _persistVm for vm ' + self.domainUuid
                  + ' on host ' + self.compute_id))
        api.vm_save(get_admin_context(), self.Vm)
        LOG.debug(_('Exiting _persistVm for vm ' + self.domainUuid
                  + ' on host ' + self.compute_id))


class LibvirtStorageVolume:

    def __init__(self,
                 connection,
                 compute_id,
                 ):

        self.libvirtconn = connection
        self.vmHost = None
        self.utils = XMLUtils()
        self.compute_id = compute_id
        self.hostUUID = None

    def processUpdates(self):
        ''' Method will iterate through the list of storage pools
        and map the data to Resource Model object "StorageVolume" '''

        LOG.debug(_('Entering processUpdates for Storage Volumes on host '
                    + self.compute_id))
        try:
            self.vmHost = InventoryCacheManager.get_object_from_cache(
                self.compute_id,
                Constants.VmHost)
            self.hostUUID = self.vmHost.get_uuid()
            hostStorageVolIds = self.vmHost.get_storageVolumeIds()
            # Checks if a storage pool already exists for the path
            # specified in nova.conf and creates the same if not present
            self._createNovaPool()
            poolList = self._getAllStoragePools()
            updatedStorageVolIds = []

            self.cur_total_storage_size = 0
            self.curr_storage_free = 0
            self.old_total_storage_size = 0
            self.old_storage_free = 0
            # Handles for new StorageVolume and Updated StorageVolume '''
            for pool in poolList:
                poolObj = self.libvirtconn.storagePoolLookupByName(pool)
                if poolObj.isActive():
                    poolObj.refresh(0)
                self._processStorage(poolObj)
                updatedStorageVolIds.append(poolObj.UUIDString())

            self.vmHost.set_storageVolumeIds(updatedStorageVolIds)
            InventoryCacheManager.update_object_in_cache(self.compute_id,
                                                         self.vmHost)

            if (self.cur_total_storage_size != self.old_total_storage_size) \
                    or (self.curr_storage_free != self.old_storage_free):
                event_api.notify_host_update(
                    event_metadata.EVENT_TYPE_HOST_UPDATED, self.vmHost)

            self.processStorageDeletes(hostStorageVolIds,
                                       updatedStorageVolIds)
        except Exception:
            LOG.error(_('Could not proceed with process updates of Storage \
            Volumes on host with id ' + self.compute_id))
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting processUpdates for Storage Volumes on host '
                    + self.compute_id))

    def _createNovaPool(self):
        """ Checks if a storage pool already exists for the path
        specified in nova.conf and creates the same if not present """

        LOG.debug(_('Entering createNovaPool for Storage Volumes on host '
                    + self.compute_id))
        # Default value for state_path is /var/lib/nova
        # Default value for instances_path is state_path + "/instances"
        novaPoolPath = getFlagByKey('instances_path')
        pools = self._getAllStoragePools()
        if len(pools) != 0:
            for poolName in pools:
                storagePool = self.libvirtconn.storagePoolLookupByName(
                    poolName)
                storageXML = storagePool.XMLDesc(0)
                path = self.utils.parseXML(storageXML, '//pool/target/path')
                if (path == novaPoolPath):
                    return
        poolName = "nova-storage-pool"
        poolXML = "<pool type='dir'>" \
            + "<name>%s</name>" % poolName \
            + " <target>" + " <path>%s</path>" % novaPoolPath \
            + " </target>" + "</pool>"
        poolobj = self.libvirtconn.storagePoolDefineXML(poolXML, 0)
        LOG.debug(_('Created storage pool '
                    + poolName + ' on host ' + self.compute_id))
        # Pool will be autostarted if host or libvirt service is restarted
        poolobj.setAutostart(1)
        # Starts the pool and changes state as active,
        # since storagePoolDefineXML creates an inactive pool by default
        poolobj.create(0)
        LOG.debug(_('Storage pool ' + poolName + ' started in path '
                    + novaPoolPath + ' on host ' + self.compute_id))
        LOG.debug(_('Exiting createNovaPool for Storage Volumes on host '
                    + self.compute_id))

    def _processStorage(self, poolObj):
        ''' Method to map the pool object to the Storage Volume Object '''

        try:
            LOG.debug(_('Entering _processStorage for Storage Volume '
                      + poolObj.UUIDString() + ' of host '
                      + self.compute_id))
            self.poolObj = poolObj
            self.storageUuid = self.poolObj.UUIDString()

            storageObjCached = \
                InventoryCacheManager.get_object_from_cache(
                    self.storageUuid,
                    Constants.StorageVolume)
            self.storageVolume = StorageVolume()

            # Sets the values into the self.storageVolume
            self._mapStorageProperties(poolObj)

            # Comparator is called to check whether the object
            # needs to be persisted or not '''
            diff_res_tup = self.utils.getdiff(
                storageObjCached,
                self.storageVolume)
            if diff_res_tup[0]:
                # Persist the StorageVolume object in cache and in DB.
                InventoryCacheManager.update_object_in_cache(
                    self.storageUuid,
                    self.storageVolume)
                self._persistStorage()
                # Generates the Events for Storage
                # added and Storage state changes
                if storageObjCached is None:

                    # Storage.Added

                    LOG.audit(_('New Storage Volume '
                              + self.storageVolume.get_id()
                              + ' added on host ' + self.compute_id))
                    event_api.notify(
                        event_metadata.EVENT_TYPE_STORAGE_ADDED,
                        self.storageVolume)
                else:
                    currConnState = \
                        self.storageVolume.get_connectionState()
                    oldConnState = \
                        storageObjCached.get_connectionState()
                    if currConnState != oldConnState:
                        if currConnState == Constants.STORAGE_STATE_ACTIVE:
                            # Storage.Enabled
                            LOG.audit(_('Storage Volume '
                                        + str(self.storageVolume.get_id())
                                        + ' on host '
                                        + str(self.compute_id) + ' enabled'
                                        ))
                            event_api.notify(
                                event_metadata.EVENT_TYPE_STORAGE_ENABLED,
                                self.storageVolume)
                        elif currConnState == Constants.STORAGE_STATE_INACTIVE:
                            # Storage.Disabled
                            LOG.audit(_('Storage Volume '
                                        + str(self.storageVolume.get_id())
                                        + ' on host ' + str(self.compute_id))
                                      + ' disabled')
                            event_api.notify(
                                event_metadata.EVENT_TYPE_STORAGE_DISABLED,
                                self.storageVolume)

                    # total/free space info of nova storage pool where
                    # nova instances will be provisioned
                    #
                    # TBD: need to aggregate size if we support multiple
                    # nova instance paths
                    storage_pool_path = self.storageVolume.\
                        get_mountPoints()[0].get_path()
                    novaPoolPath = getFlagByKey('instances_path')
                    if (storage_pool_path == novaPoolPath):
                        self.cur_total_storage_size = \
                            long(self.storageVolume.get_size())
                        self.curr_storage_free = \
                            long(self.storageVolume.get_free())
                        self.old_total_storage_size = \
                            long(storageObjCached.get_size())
                        self.old_storage_free = \
                            long(storageObjCached.get_free())
        except Exception:
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting _processStorage for Storage Volume '
                  + self.storageUuid + ' of host ' + self.compute_id))

    def _mapStorageProperties(self, poolObj):
        ''' Mapping attributes for StorageVolume '''

        LOG.debug(_('Entering _mapStorageProperties for Storage Volume '
                    + self.storageUuid + ' of host ' + self.compute_id))
        self.storageVolume.set_resourceManagerId(self.hostUUID)
        self.storageVolume.set_id(self.poolObj.UUIDString())
        self.storageVolume.set_name(self.poolObj.name())

        if self.poolObj.isActive():
            self.storageVolume.set_connectionState(
                Constants.STORAGE_STATE_ACTIVE)
        else:
            self.storageVolume.set_connectionState(
                Constants.STORAGE_STATE_INACTIVE)

        storageXML = self.poolObj.XMLDesc(0)

        # Call the setter methods to pass the StoragePool Xml and
        # set in self.StorageVolume
        self.storageVolume.set_name(self.utils.parseXML(storageXML,
                                    '//pool/name'))

        hostMountPoint = HostMountPoint()
        hostMountPoint.set_path(self.utils.parseXML(storageXML,
                                '//pool/target/path'))
        hostMountPoint.set_vmHostId(self.compute_id)
        self.storageVolume.get_mountPoints().append(hostMountPoint)

        self.storageVolume.set_size(self.utils.parseXML(storageXML,
                                    '//pool/capacity'))
        self.storageVolume.set_free(self.utils.parseXML(storageXML,
                                    '//pool/available'))

        self.storageVolume.set_assignedServerCount(1)
        self.storageVolume.set_shared(False)

        # self.storageVolume.set_volumeType("DAS")

        self.storageVolume.set_volumeType(
            self.utils.parseXMLAttributes(storageXML,
                                          '//pool', 'type').upper())
        self.storageVolume.set_volumeId(self.storageUuid)
        LOG.debug(_('Exiting _mapStorageProperties for Storage Volume '
                    + self.storageUuid + ' of host ' + self.compute_id))

    def processStorageDeletes(self, hostStorageVolIds,
                              updatedStorageVolIds):
        LOG.debug(_('Entering processStorageDeletes of \
        Storage Volumes of host ' + self.compute_id))

        # Should identify storageVolumes which have been deleted
        # Should remove the corresponding storage object from cache and DB
        # Should update the host object's storageVolume list
        # in both cache and DB

        deletion_list = self.utils.getDeletionList(
            hostStorageVolIds,
            updatedStorageVolIds)

        if len(deletion_list) != 0:

            # Delete object from cache

            storage_deleted_list = []
            for storageId in deletion_list:
                obj = \
                    InventoryCacheManager.get_object_from_cache(
                        storageId,
                        Constants.StorageVolume)
                if obj is not None:
                    storage_deleted_list.append(obj)
                InventoryCacheManager.delete_object_in_cache(
                    storageId,
                    Constants.StorageVolume)
            api.storage_volume_delete_by_ids(
                get_admin_context(),
                deletion_list)
            # Generate storage deleted event
            for storage_deleted in storage_deleted_list:
                LOG.audit(_('Storage volume '
                            + str(storage_deleted.get_id())
                            + ' deleted on host '
                            + str(self.compute_id)))
                event_api.notify(event_metadata.EVENT_TYPE_STORAGE_DELETED,
                                 storage_deleted)
        LOG.debug(_('Exiting processStorageDeletes of Storage Volumes of host '
                    + self.compute_id))

    def _persistStorage(self):
        LOG.debug(_('Entering _persistStorage for Storage Volume '
                  + self.storageUuid + ' on host ' + self.compute_id))
        api.storage_volume_save(get_admin_context(), self.storageVolume)
        LOG.debug(_('Exiting _persistStorage for Storage Volume '
                  + self.storageUuid + ' on host ' + self.compute_id))

    def _getAllStoragePools(self):
        """ Lists all active and inactive storage pools """
        poolList = self.libvirtconn.listStoragePools()
        inactivePoolList = self.libvirtconn.listDefinedStoragePools()
        if len(inactivePoolList) > 0:
            for pool in inactivePoolList:
                poolList.append(pool)
        return poolList


class LibvirtNetwork:

    ''' LibvirtNetwork class to collect network inventory '''

    def __init__(self,
                 connection,
                 compute_id,
                 ):

        self.rmContext = InventoryCacheManager.get_compute_inventory(
            compute_id).compute_rmcontext
        self.libvirtconn = connection
        self.vmHost = None
        self.hostUUID = None
        self.utils = XMLUtils()
        self.cachedSubnetIds = []
        self.updatedSubnetIds = []
        self.compute_id = compute_id
        self.ipProfiles = []
        self.vswitches = []
        self.portGroups = []
#        self.vmHost = vmHost

    def processUpdates(self):
        ''' Method will iterate through the list of libvirt network objects
        and map the data to Resource Model objects
        "Virtual Switch" and "Subnet" '''

        LOG.debug(_('Entering processUpdates of Network for host '
                  + self.compute_id))
        try:
            self.cachedVmHost = \
                InventoryCacheManager.get_object_from_cache(
                    self.compute_id,
                    Constants.VmHost)
            self.vmHost = copy.deepcopy(self.cachedVmHost)
            self.hostUUID = self.vmHost.get_uuid()
            cachedSwitches = self.vmHost.get_virtualSwitches()

            for switch in cachedSwitches:
                self.cachedSubnetIds.append('Subnet_' + switch.get_id())

            networks = self.libvirtconn.listNetworks()
            inactiveNetworks = self.libvirtconn.listDefinedNetworks()
            if len(inactiveNetworks) > 0:
                for net in inactiveNetworks:
                    networks.append(net)

            # Inventory collection for new virtual networks and
            # updated virtual networks

            for net in networks:
                networkObj = self.libvirtconn.networkLookupByName(net)
                self._processVirtualNetwork(networkObj)

            interfaces = self.libvirtconn.listInterfaces()
            inactiveInterfaces = self.libvirtconn.listDefinedInterfaces()
            if len(inactiveInterfaces) > 0:
                for net in inactiveInterfaces:
                    interfaces.append(net)

            # Inventory collection for new virtual networks and
            # updated virtual networks

            for net in interfaces:
                interfaceObj = self.libvirtconn.interfaceLookupByName(net)
                self._processNetworkInterface(interfaceObj)

            self.vmHost.set_ipAddresses(self.ipProfiles)
            self.vmHost.set_virtualSwitches(self.vswitches)
            self.vmHost.set_portGroups(self.portGroups)
            if self.utils.getdiff(self.cachedVmHost, self.vmHost)[0]:
                # Perist the Host object in cache and in DB.
                InventoryCacheManager.update_object_in_cache(
                    str(self.vmHost.get_id()),
                    self.vmHost)
                self._persistVmHost()
                self._processNetworkEvents(self.cachedVmHost, self.vmHost)

            self._processNetworkDeletes(self.cachedSubnetIds,
                                        self.updatedSubnetIds)
        except Exception:
            LOG.error(_('Could not proceed with process updates of \
            Network on host with id ' + self.compute_id))
            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting processUpdates of Network of host '
                  + self.compute_id))

    def _processNetworkEvents(self, oldobj, newobj):
        ''' Generates the Events for Network added and Network deleted '''

        LOG.debug(_('Entering NetworkEvents of host '
                  + self.compute_id))
        update = '_update'
        virtualSwitches = 'virtualSwitches'
        add = '_add'
        delete = '_delete'
        portGroups = 'portGroups'
        connectionState = 'connectionState'
        diff_tup = self.utils.getdiff(oldobj, newobj)
        diffdict = diff_tup[1]
        if diffdict is not None and update in diffdict and\
                virtualSwitches in diffdict[update]:
            if add in diffdict[update][virtualSwitches]:
                for vswitch in \
                        diffdict[update][
                            virtualSwitches][add].values():
                    # Network.Added
                    LOG.audit(_('New Network '
                                + str(vswitch.get_name())
                                + ' added on host '
                                + self.compute_id))
                    event_api.notify(
                        event_metadata.EVENT_TYPE_NETWORK_ADDED,
                        vswitch, host_id=self.compute_id)

            if delete in diffdict[update][virtualSwitches]:
                for vswitch in \
                        diffdict[update][
                            virtualSwitches][delete].values():
                    # Network.Deleted
                    LOG.audit(_('Network '
                                + str(vswitch.get_name())
                                + ' deleted on host '
                                + self.compute_id))
                    event_api.notify(
                        event_metadata.EVENT_TYPE_NETWORK_DELETED,
                        vswitch, host_id=self.compute_id)

            if update in diffdict[update][virtualSwitches]:
                for vswitchid in \
                        diffdict[update][virtualSwitches][update]:
                    for vswitch in newobj.get_virtualSwitches():
                        if vswitchid == vswitch.get_id():
                            if connectionState in diffdict[
                                    update][virtualSwitches][
                                        update][vswitchid][update]:
                                # Network.Enabled
                                if diffdict[update][virtualSwitches][
                                        update][vswitchid][
                                            update][connectionState] \
                                        == Constants.\
                                        VIRSWITCH_STATE_ACTIVE:
                                    LOG.audit(_('Network '
                                                + str(vswitch.
                                                      get_name())
                                                + ' enabled on host '
                                                + self.compute_id))
                                    event_api.notify(
                                        event_metadata.
                                        EVENT_TYPE_NETWORK_ENABLED,
                                        vswitch,
                                        host_id=self.compute_id)
                                # Network.Disabled
                                if diffdict[update][virtualSwitches][update][
                                        vswitchid][update][
                                            connectionState] == \
                                        Constants.VIRSWITCH_STATE_INACTIVE:
                                    LOG.audit(_('Network '
                                                + str(vswitch.get_name())
                                                + ' disabled on host '
                                                + self.compute_id))
                                    event_api.\
                                        notify(event_metadata.
                                               EVENT_TYPE_NETWORK_DISABLED,
                                               vswitch,
                                               host_id=self.compute_id)
                            break

        if diffdict is not None and update in diffdict and\
                portGroups in diffdict[update]:
            if add in diffdict[update][portGroups]:
                for portGroup in \
                        diffdict[update][portGroups][add].values():
                    # PortGroup.Added
                    LOG.audit(_('New PortGroup '
                                + str(portGroup.get_name())
                                + ' added to virtual switch '
                                + str(portGroup.get_virtualSwitchId())
                                + ' on host ' + self.compute_id))
                    event_api.notify(
                        event_metadata.EVENT_TYPE_PORTGROUP_ADDED,
                        portGroup)

            if delete in diffdict[update][portGroups]:
                for portGroup in \
                        diffdict[update][portGroups][delete].values():
                    # PortGroup.Deleted
                    LOG.audit(_('PortGroup '
                                + str(portGroup.get_name())
                                + ' deleted from virtual switch '
                                + str(portGroup.get_virtualSwitchId())
                                + ' on host ' + self.compute_id))
                    event_api.notify(
                        event_metadata.EVENT_TYPE_PORTGROUP_DELETED,
                        portGroup)

            if update in diffdict[update][portGroups]:
                for portGroupid in \
                        diffdict[update][portGroups][update]:
                    # PortGroup.Reconfigured
                    for portGroup in newobj.get_portGroups():
                        if portGroupid == portGroup.get_id():
                            changed_attr = \
                                events_util.getChangedAttributesForUpdateEvent(
                                    portGroup,
                                    diffdict[update][portGroups][
                                        update][portGroupid])
                            if changed_attr is not None and\
                                    len(changed_attr) > 0:
                                LOG.audit(_('Port group '
                                            + str(portGroup.get_name())
                                            + ' attached to virtual switch '
                                            + str(portGroup.
                                                  get_virtualSwitchId())
                                            + ' on host ' + self.compute_id
                                            + ' is reconfigured'))
                                event_api.notify(
                                    event_metadata.
                                    EVENT_TYPE_PORTGROUP_RECONFIGURED,
                                    portGroup, changed_attributes=changed_attr)
        LOG.debug(_('Exiting NetworkEvents of host ' + self.compute_id))

    def _processNetworkInterface(self, interfaceObj):
        LOG.debug(_('Entering _processNetworkInterface of Networks on host '
                    + self.compute_id))
        interfaceXML = interfaceObj.XMLDesc(0)
        swType = self.utils.parseXMLAttributes(interfaceXML,
                                               '//interface', 'type')
        if swType.lower() == 'bridge':
            self.vswitch = VirtualSwitch()
            self.subnet = Subnet()
            self.portGroup = PortGroup()
            self.vswitch.set_id(str(interfaceObj.MACString()))
            self.subnet.set_id('Subnet_' + interfaceObj.MACString())
            self.portGroup.set_id('PortGroup_'
                                  + interfaceObj.MACString())
            self.vswitch.set_name(str(interfaceObj.name()))
            self.subnet.set_name(str(interfaceObj.name()))
            self.portGroup.set_name(str(interfaceObj.name()))
            self.subnet.set_networkAddress(self.vswitch.get_id())
            self.vswitch.set_resourceManagerId(str(self.hostUUID))
            self.subnet.set_resourceManagerId(str(self.hostUUID))
            self.portGroup.set_resourceManagerId(str(self.hostUUID))
            self.subnet.add_networkSources('VS_NETWORK')
            interfaces = self.utils.getNodeXML(
                interfaceXML,
                "//interface/bridge/interface[@type='ethernet']")
            for element in interfaces:
                interfaceNode = str(element)
                interfaceName = \
                    self.utils.parseXMLAttributes(
                        interfaceNode,
                        '//interface', 'name')
                mac = self.utils.parseXMLAttributes(interfaceNode,
                                                    '//interface/mac',
                                                    'address')
                if self.vswitch.get_id() == mac:
                    self.vswitch.get_networkInterfaces().append(interfaceName)
                    break

            self.portGroup.set_virtualSwitchId(self.vswitch.get_id())

            self.subnetObjCached = \
                InventoryCacheManager.get_object_from_cache(
                    str(self.subnet.get_id()), Constants.Network)
            if interfaceObj.isActive():
                self.vswitch.set_connectionState(
                    Constants.VIRSWITCH_STATE_ACTIVE)
            else:
                self.vswitch.set_connectionState(
                    Constants.VIRSWITCH_STATE_INACTIVE)
            self.vswitch.set_switchType(swType)
            self.vswitch.add_subnetIds(self.subnet.get_id())
            self.vswitch.get_portGroups().append(self.portGroup)
            self.vswitches.append(self.vswitch)
            self.portGroups.append(self.portGroup)
            self.updatedSubnetIds.append(self.subnet.get_id())
            if self.utils.getdiff(self.subnetObjCached, self.subnet)[0]:
                InventoryCacheManager.update_object_in_cache(
                    str(self.subnet.get_id()), self.subnet)
                self._persistNetwork()
        # Mapping IP profile for host

        name = self.utils.parseXMLAttributes(interfaceXML,
                                             '//interface', 'name')

        # Ignoring loopback

        if name != 'lo':
            protocolNodes = self.utils.getNodeXML(interfaceXML,
                                                  '//interface/protocol')
            for protocol in protocolNodes:
                ipNodes = self.utils.getNodeXML(str(protocol),
                                                '//protocol/ip')
                for element in ipNodes:
                    ipProfile = IpProfile()
                    ipProfile.set_ipAddress(
                        self.utils.parseXMLAttributes(str(element),
                                                      '//ip', 'address'))
                    ipProfile.set_hostname(
                        str(self.rmContext.rmIpAddress))
                    ipProfile.set_ipType(
                        self._getIpType(ipProfile.get_ipAddress()))
                    self.ipProfiles.append(ipProfile)

        LOG.debug(_('Exiting _processNetworkInterface of Networks on host '
                    + self.compute_id))

    def _processVirtualNetwork(self, networkObj):
        LOG.debug(_('Entering _processVirtualNetwork of Networks on host '
                    + self.compute_id))

        networkXML = networkObj.XMLDesc(0)
        self.vswitch = VirtualSwitch()
        self.subnet = Subnet()
        self.portGroup = PortGroup()

        self.vswitch.set_id(str(self.utils.parseXMLAttributes(networkXML,
                            '//network/mac', 'address')))
        self.subnet.set_id('Subnet_' + self.vswitch.get_id())
        self.portGroup.set_id('PortGroup_' + self.vswitch.get_id())
        self.subnet.set_networkAddress(self.vswitch.get_id())

        self.subnetObjCached = \
            InventoryCacheManager.get_object_from_cache(
                str(self.subnet.get_id()), Constants.Network)

        if networkObj.isActive():
            self.vswitch.set_connectionState('Active')
        else:
            self.vswitch.set_connectionState('Inactive')

        if networkObj.autostart():
            self.subnet.set_isBootNetwork(True)
        else:
            self.subnet.set_isBootNetwork(False)

        self._mapVirtualNetworkProperties(networkXML)

        # Comparator is called to check whether the
        # object needs to be persisted or not

        if self.utils.getdiff(self.subnetObjCached, self.subnet)[0]:
            InventoryCacheManager.update_object_in_cache(
                str(self.subnet.get_id()), self.subnet)
            self._persistNetwork()
        LOG.debug(_('Exiting _processVirtualNetwork of Networks on host '
                    + self.compute_id))

    def _mapVirtualNetworkProperties(self, networkXML):
        LOG.debug(_('Entering _mapVirtualNetworkProperties of \
        Networks on host ' + self.compute_id))
        self.vswitch.set_name(self.utils.parseXML(networkXML,
                              '//network/name'))
        self.subnet.set_name(self.vswitch.get_name())
        self.portGroup.set_name(self.vswitch.get_name())
        self.vswitch.set_resourceManagerId(str(self.hostUUID))
        self.subnet.set_resourceManagerId(str(self.hostUUID))
        self.portGroup.set_resourceManagerId(str(self.hostUUID))
        self.subnet.add_networkSources('VS_NETWORK')
        self.portGroup.set_virtualSwitchId(self.vswitch.get_id())
        self.vswitch.set_switchType(self.utils.parseXMLAttributes(networkXML,
                                    '//network/forward', 'mode'))
        gateway = self.utils.parseXMLAttributes(networkXML,
                                                '//network/ip', 'address')
        self.subnet.add_defaultGateways(str(gateway))
        self.subnet.set_networkMask(self.utils.parseXMLAttributes(networkXML,
                                    '//network/ip', 'netmask'))
        ipRange = IpAddressRange()
        if self.utils.parseXMLAttributes(networkXML,
                                         '//network/ip/dhcp/range',
                                         'start') is not None:
            startIpAddress = IpAddress()
            startIpAddress.set_address(
                self.utils.parseXMLAttributes(
                    networkXML,
                    '//network/ip/dhcp/range',
                    'start'))
            ipRange.set_id(startIpAddress.get_address())
            startIpAddress.set_id(startIpAddress.get_address())
            startIpAddress.set_allocationType('DHCP')
            ipRange.set_startAddress(startIpAddress)
            endIpAddress = IpAddress()
            endIpAddress.set_address(
                self.utils.parseXMLAttributes(
                    networkXML,
                    '//network/ip/dhcp/range',
                    'end'))
            endIpAddress.set_id(endIpAddress.get_address())
            endIpAddress.set_allocationType('DHCP')
            ipRange.set_endAddress(endIpAddress)
            ipRange.set_allocationType('DHCP')
        else:
            ipRange.set_id(self.subnet.get_id() + '_AUTO_STATIC')
            ipRange.set_allocationType('AUTO_STATIC')

        self.subnet.get_ipAddressRanges().append(ipRange)
        self.subnet.set_ipType(
            self._getIpType(self.subnet.get_defaultGateways()[0]))
        self.vswitch.get_subnetIds().append(self.subnet.get_id())
        self.vswitch.get_portGroups().append(self.portGroup)

        self.vswitches.append(self.vswitch)
        self.portGroups.append(self.portGroup)
        InventoryCacheManager.update_object_in_cache(
            str(self.subnet.get_id()), self.subnet)
        self.updatedSubnetIds.append(self.subnet.get_id())
        LOG.debug(_('Exiting _mapVirtualNetworkProperties of Networks on host '
                    + self.compute_id))

    def _getIpType(self, address):
        if ':' in address:
            return 'IPV6'
        elif '.' in address:
            return 'IPV4'
        else:
            return 'UNSPECIFIED'

    def _persistNetwork(self):
        LOG.debug(_('Entering _persistNetwork for Network '
                  + str(self.subnet.get_id)))
        try:
            api.subnet_save(get_admin_context(), self.subnet)
        except Exception:

#           api.virtual_switch_save(get_admin_context(), self.vswitch)

            self.utils.log_error(traceback.format_exc())
        LOG.debug(_('Exiting _persistNetwork for Network '
                  + str(self.subnet.get_id)))

    def _persistVmHost(self):
        LOG.debug(_('Entering _persist for host uuid '
                  + self.compute_id))
        api.vm_host_save(get_admin_context(), self.vmHost)
        LOG.debug(_('Exiting _persist for host uuid '
                  + self.compute_id))

    def _processNetworkDeletes(self,
                               cachedSubnetIds,
                               updatedSubnetIds):

        LOG.debug(_('Entering processNetworkDeletes of Networks for host '
                    + self.compute_id))

        # Should identify Subnets and vswitches which have been deleted
        # Should remove the corresponding subnet object from cache and DB
        # Should remove the corresponding vswitch object from DB

        try:
            deletion_list_subnets = \
                self.utils.getDeletionList(cachedSubnetIds,
                                           updatedSubnetIds)

            if len(deletion_list_subnets) != 0:

                # Delete objects from cache

                for subnetId in deletion_list_subnets:
                    InventoryCacheManager.delete_object_in_cache(
                        subnetId,
                        Constants.Network)

                # Delete objects from DB

                api.subnet_delete_by_ids(get_admin_context(),
                                         deletion_list_subnets)
        except Exception:

            self.utils.log_error(traceback.format_exc())

        LOG.debug(_('Exiting processNetworkDeletes of Networks for host '
                    + self.compute_id))
