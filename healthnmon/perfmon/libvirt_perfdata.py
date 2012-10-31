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

"""Module responsible for collecting performance data of KVM Host andVm from libvirt"""

from healthnmon.resourcemodel.healthnmonResourceModel import ResourceUtilization
from healthnmon.utils import XMLUtils
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.events import api as event_api
from healthnmon.events import event_metadata
from healthnmon.constants import Constants
from healthnmon.perfmon.perf_stats import Stats
from healthnmon import log
from nova import flags
import time
import datetime
import paramiko


FLAGS = flags.FLAGS
LOG = log.getLogger('healthnmon.libvirt_perfdata')


class LibvirtPerfMonitor:

    perfDataCache = {}

    @staticmethod
    def get_perfdata_fromCache(uuid, stats_type):
        LOG.debug(_(' Entering into get_perfdata_fromCache for uuid  '
                  + uuid))
        if uuid in LibvirtPerfMonitor.perfDataCache:
            return LibvirtPerfMonitor.perfDataCache[uuid][stats_type]

    @staticmethod
    def update_perfdata_InCache(uuid, old_stats, new_stats):
        LOG.debug(_(' Entering into update_perfdata_InCache for uuid '
                  + uuid))
        if uuid in LibvirtPerfMonitor.perfDataCache:
            LibvirtPerfMonitor.perfDataCache[uuid][Constants.OLD_STATS] = \
                old_stats
            LibvirtPerfMonitor.perfDataCache[uuid][Constants.NEW_STATS] = \
                new_stats

        LOG.debug(_(' Exiting into update_perfdata_InCache for uuid '
                  + uuid))

    @staticmethod
    def delete_perfdata_fromCache(uuid):
        LOG.debug(_(' Entering into delete_object_in_cache for uuid = '
                  + uuid))
        if uuid in LibvirtPerfMonitor.perfDataCache:
            del LibvirtPerfMonitor.perfDataCache[uuid]
        LOG.debug(_(' Exiting from delete_object_in_cache for uuid '
                  + uuid))

    def refresh_perfdata(
        self,
        conn,
        uuid,
        perfmon_type,
        ):
        '''Refreshes the performance data  '''

        LOG.info(_('Entering refresh_perfdata for uuid :' + uuid))
        if uuid not in LibvirtPerfMonitor.perfDataCache:
            LibvirtPerfMonitor.perfDataCache[uuid] = \
                {Constants.OLD_STATS: None, Constants.NEW_STATS: None}

        if perfmon_type == Constants.VmHost:
            LibvirtVmHostPerfData(conn, uuid).refresh_perfdata()
            host_obj = InventoryCacheManager.get_object_from_cache(uuid,
                Constants.VmHost)
            if host_obj is not None:
                event_api.notify_host_update(event_metadata.EVENT_TYPE_HOST_UPDATED, host_obj)
        elif perfmon_type == Constants.Vm:
            LibvirtVmPerfData(conn, uuid).refresh_perfdata()
        LOG.info(_('Exiting refresh_perfdata for uuid :' + uuid))

    def get_resource_utilization(
        self,
        uuid,
        perfmon_type,
        window_minutes,
        ):
        '''Returns the sampled performance data of KVM host '''

        LOG.debug(_('Entering get_resource_utilization for uuid '
                  + uuid))
        if perfmon_type == Constants.VmHost:
            return SamplePerfData().sample_host_perfdata(uuid,
                    window_minutes)
        elif perfmon_type == Constants.Vm:
            return SamplePerfData().sample_vm_perfdata(uuid,
                    window_minutes)


class LibvirtVmHostPerfData:

    """ Responsible for collecting KVM VM Host Performance data from libvirt """

    def __init__(self, conn, uuid):
        self.conn = conn
        self.libvirtconn = conn
        self.uuid = uuid
        self.hostObj = None
        self.old_stats = None
        self.new_stats = None
        self.temp_stats = Stats()
        self.utils = XMLUtils()

    def refresh_perfdata(self):
        """ Responsible for refreshing Memory statistics of KVM Vm Host"""

        LOG.debug(_('Entering refresh_perfdata for vm host  '
                  + self.uuid))

        self._update_hostmemory_stats()

        self.temp_stats.timestamp = time.time()
        self.old_stats = self.new_stats
        self.new_stats = self.temp_stats

        LibvirtPerfMonitor.update_perfdata_InCache(self.uuid,
                self.old_stats, self.new_stats)
        LOG.debug(_('Exiting refresh_perfdata for vm host '
                  + self.uuid))

    def _update_hostmemory_stats(self):
        memstats = {}
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn_driver = InventoryCacheManager.get_compute_inventory(self.uuid).get_compute_conn_driver()
        ssh.connect(conn_driver.compute_rmcontext.rmIpAddress,
                    username=conn_driver.compute_rmcontext.rmUserName,
                    password=conn_driver.compute_rmcontext.rmPassword)

        LOG.debug(_('Connected to host using paramiko'))
        (stdin, stdout, stderr) = ssh.exec_command('virsh nodememstats')
        type(stdin)
        error = stderr.readlines()
        ssh.close()
        if len(error) == 0:
            nodememstats = stdout.readlines()
            for memstat in nodememstats:
                memstatList = memstat.split()
                if len(memstatList) > 0:
                    memstats[memstatList[0]] = memstatList[len(memstatList) - 2]
            self.temp_stats.totalMemory = int(memstats['total'])
            self.temp_stats.freeMemory = int(memstats['free']) + int(memstats['buffers:']) + int(memstats['cached'])
            LOG.debug(_('Total Memory:' + str(self.temp_stats.totalMemory) + ', Free Memory:' + str(self.temp_stats.freeMemory)))
        else:
            LOG.debug(_('Error occurred in connecting vmhost via ssh %s')
                      % error)
            self.temp_stats.status = -1


class LibvirtVmPerfData:

    """ Responsible for collecting KVM VM Performance data from libvirt """

    def __init__(self, conn, uuid):
        self.conn = conn
        self.libvirtconn = conn
        self.uuid = uuid
        self.domainObj = None
        self.old_stats = None
        self.new_stats = None
        self.temp_stats = Stats()
        self.utils = XMLUtils()

    def refresh_perfdata(self):
        """ Responsible for refreshing CPU,Disk,Network,Memory statistics of KVM Vm """

        self.domainObj = self.libvirtconn.lookupByUUIDString(self.uuid)
        LOG.debug(_('Entering refresh_perfdata for vm '
                  + self.domainObj.name()))

        self.old_stats = \
            LibvirtPerfMonitor.get_perfdata_fromCache(self.uuid,
                Constants.OLD_STATS)
        self.new_stats = \
            LibvirtPerfMonitor.get_perfdata_fromCache(self.uuid,
                Constants.NEW_STATS)
        info = None
        vmXML = None
        try:
            info = self.domainObj.info()
            vmXML = self.domainObj.XMLDesc(0)
        except Exception, err:
            LOG.error(_("Error reading domain info and XML for '%s': %s"
                       % (self.domainObj.name(), err)))

        if info is not None and vmXML is not None:
            self._update_cpu_stats(info, vmXML)
            self._update_disk_stats(vmXML)
            self._update_net_stats(vmXML)
            self._update_memory_stats(vmXML)
        else:
            LOG.error(_("Error reading CPU,disk, net stats for '%s'"
                      % self.domainObj.name()))
            self.temp_stats.status = -1

        self.temp_stats.timestamp = time.time()
        self.old_stats = self.new_stats
        self.new_stats = self.temp_stats

        LibvirtPerfMonitor.update_perfdata_InCache(self.uuid,
                self.old_stats, self.new_stats)
        LOG.debug(_('Exiting refresh_perfdata for vm '
                  + self.domainObj.name()))

    def _update_cpu_stats(self, domain_info, vmXML):
        LOG.debug(_('Entering _update_cpu_stats for VM  '
                  + self.domainObj.name()))

        self.temp_stats.cpuStats.cycles['user'] = domain_info[4]
        self.temp_stats.cpuPerfTime = time.time()
        self.temp_stats.ncpus = self.utils.parseXML(vmXML, "//domain/vcpu")

        LOG.debug(_('Exiting _update_cpu_stats for VM  '
                  + self.domainObj.name()))

    def _update_disk_stats(self, vmXML):
        LOG.debug(_('Entering _update_disk_stats for VM  '
                  + self.domainObj.name()))
        rd = 0
        wr = 0

        disksAttached = self.utils.getNodeXML(vmXML,
                "//domain/devices/disk[@device='disk']")
        for disk in disksAttached:
            diskXmlStr = str(disk)
            dev = self.utils.parseXMLAttributes(diskXmlStr,
                    '//disk/target', 'dev')
            try:
                io = self.domainObj.blockStats(dev)
                if io:
                    rd += io[1]
                    wr += io[3]
            except Exception, err:
                LOG.error(_("Error reading disk stats for '%s' dev '%s': %s"
                           % (self.domainObj.name(), dev, err)))
                self.temp_stats.status = -1
                break

        self.temp_stats.diskReadBytes = rd
        self.temp_stats.diskWriteBytes = wr
        self.temp_stats.diskPerfTime = time.time()
        LOG.debug(_('Exiting _update_disk_stats for VM  '
                  + self.domainObj.name()))

    def _update_net_stats(self, vmXML):
        LOG.debug(_('Entering _update_net_stats for VM  '
                  + self.domainObj.name()))
        rx = 0
        tx = 0

        vmNetAdapterAttached = self.utils.getNodeXML(vmXML,
                '//domain/devices/interface')
        for netAdapter in vmNetAdapterAttached:
            interfaceXml = str(netAdapter)
            dev = self.utils.parseXMLAttributes(interfaceXml,
                    '//interface/target', 'dev')

            try:
                io = self.domainObj.interfaceStats(dev)
                if io:
                    rx += io[0]
                    tx += io[4]
            except Exception, err:
                LOG.error(_("Error reading net stats for '%s' dev '%s': %s"
                           % (self.domainObj.name(), dev, err)))
                self.temp_stats.status = -1
                break

        self.temp_stats.netReceivedBytes = rx
        self.temp_stats.netTransmittedBytes = tx
        self.temp_stats.netPerfTime = time.time()
        LOG.debug(_('Exiting _update_net_stats for VM  '
                  + self.domainObj.name()))

    def _update_memory_stats(self, vmXML):
        total_memory = long(self.utils.parseXML(vmXML, '//domain/memory'
                            ))
        memory_consumed = long(self.utils.parseXML(vmXML,
                               '//domain/currentMemory'))

        self.temp_stats.totalMemory = total_memory
        self.temp_stats.freeMemory = total_memory - memory_consumed


class SamplePerfData:

    def __init__(self):
        self.resource_utilization = None

    def sample_host_perfdata(self, uuid, window_minutes):
        LOG.info(_('Entering sample_host_perfdata for VM Host '
                  + uuid))
        cpuTime = 0
        prevcpuTime = 0
        diskRead = 0
        diskWrite = 0
        netRead = 0
        netWrite = 0
        pcentHostCpu = 0.0
        totalMemory = 0
        freeMemory = 0

        self.resource_utilization = ResourceUtilization()
        self._set_resource_utilization_defaults(uuid)
        self.timestamp = time.time()
        vm_stats_timestamp = None
        vm_stats_oldtimestamp = None
        host_obj = InventoryCacheManager.get_object_from_cache(uuid,
                Constants.VmHost)

        if host_obj.get_connectionState() == 'Disconnected':
            LOG.info(_('Host ' + uuid + ' is disconnected'))
            self.resource_utilization.set_status(-1)
            return self.resource_utilization
        # Host Performance data is calculated aggregating the performance data collected for VM's'''
        for vm_id in host_obj.get_virtualMachineIds():
            vm_obj = InventoryCacheManager.get_object_from_cache(vm_id,
                    Constants.Vm)
            # Check if VM is in running state, else skip the performance data for that VM
            if vm_obj.get_powerState() == Constants.VM_POWER_STATES[1]:
                #Check if VM has old stats for sampling, else performance data is not valid
                if LibvirtPerfMonitor.get_perfdata_fromCache(vm_id,
                        Constants.OLD_STATS) is not None:
                    vm_stats_timestamp = \
                        LibvirtPerfMonitor.get_perfdata_fromCache(vm_id,
                            Constants.NEW_STATS).timestamp
                    vm_stats_oldtimestamp = \
                        LibvirtPerfMonitor.get_perfdata_fromCache(vm_id,
                            Constants.OLD_STATS).timestamp
                    LOG.debug(_('VM last sampled time stamp '
                              + str(vm_stats_timestamp)))

                    # Check if the VM performance data is collected in last 5 minutes(considering buffer of 1 minute) and,
                    # status of the VM performance data, else performance data for VM is stale and is not valid
                    if self.timestamp - vm_stats_timestamp \
                        < FLAGS.perfmon_refresh_interval + 60 \
                        and LibvirtPerfMonitor.get_perfdata_fromCache(vm_id,
                            Constants.NEW_STATS).status == 0:
                        LOG.debug(_('Aggregating using performance data of VM '
                                   + vm_id))
                        (vmdiskRead, vmdiskWrite) = \
                            self._sample_disk_stats(vm_id)
                        (vmnetRead, vmnetWrite) = \
                            self._sample_net_stats(vm_id)
                        diskRead += vmdiskRead
                        diskWrite += vmdiskWrite
                        netRead += vmnetRead
                        netWrite += vmnetWrite
                        cpuTime += \
                            LibvirtPerfMonitor.get_perfdata_fromCache(vm_id,
                                Constants.NEW_STATS).cpuStats.cycles['user'
                                ]
                        prevcpuTime += \
                            LibvirtPerfMonitor.get_perfdata_fromCache(vm_id,
                                Constants.OLD_STATS).cpuStats.cycles['user'
                                ]
                        self.resource_utilization.set_status(0)
                    else:
                        LOG.error(_('Performance data of VM '
                                  + vm_id + ' is not valid '))
                        self.resource_utilization.set_status(-1)
                        break
                else:
                    LOG.error(_('Performance data of VM ' + vm_id
                              + ' is not yet sampled'))
                    self.resource_utilization.set_status(-1)
                    break
            else:
                LOG.info(_('VM ' + vm_id
                          + ' is not running. Skipping performance data of VM for host perf data'
                          ))
                self.resource_utilization.set_status(0)

        host_cpus = host_obj.get_processorCoresCount()
        if self.resource_utilization.status == 0:
            if vm_stats_timestamp is not None and vm_stats_oldtimestamp \
                is not None:
                pcentHostCpu = (cpuTime - prevcpuTime) * 100.0 \
                    / ((vm_stats_timestamp - vm_stats_oldtimestamp)
                       * 1000.0 * 1000.0 * 1000.0)
                pcentHostCpu = pcentHostCpu / int(host_cpus)

                pcentHostCpu = max(0.0, min(100.0, pcentHostCpu))
        host_cpu_speed = host_obj.get_processorSpeedMhz()
        self.resource_utilization.set_cpuUserLoad(pcentHostCpu)
        self.resource_utilization.set_ncpus(host_cpus)
        self.resource_utilization.set_hostCpuSpeed(host_cpu_speed)
        self.resource_utilization.set_hostMaxCpuSpeed(host_cpu_speed)
        self.resource_utilization.set_diskRead(diskRead)
        self.resource_utilization.set_diskWrite(diskWrite)
        self.resource_utilization.set_netRead(netRead)
        self.resource_utilization.set_netWrite(netWrite)
        self.resource_utilization.set_resourceId(uuid)
        self.resource_utilization.set_granularity(window_minutes)
        if (LibvirtPerfMonitor.get_perfdata_fromCache(uuid, Constants.NEW_STATS) is not None) and \
            (LibvirtPerfMonitor.get_perfdata_fromCache(uuid, Constants.NEW_STATS).status == 0):
            totalMemory = LibvirtPerfMonitor.get_perfdata_fromCache(uuid, Constants.NEW_STATS).totalMemory
            freeMemory = LibvirtPerfMonitor.get_perfdata_fromCache(uuid, Constants.NEW_STATS).freeMemory
        self.resource_utilization.set_totalMemory(totalMemory)
        self.resource_utilization.set_freeMemory(freeMemory)
        self.resource_utilization.set_configuredMemory(totalMemory)

        '''While all the VMs are in shutoff state the timestamp being shown is the
        current time stamp '''
        if vm_stats_timestamp is not None:
            self.resource_utilization.set_timestamp(datetime.datetime.utcfromtimestamp(vm_stats_timestamp))
        else:
            self.resource_utilization.set_timestamp(time.time())
        LOG.info(_('Exiting sample_host_perfdata for VM Host ' + uuid))
        return self.resource_utilization

    def sample_vm_perfdata(self, uuid, window_minutes):
        LOG.info(_('Entering sample_vm_perfdata for VM ' + uuid))
        self.resource_utilization = ResourceUtilization()
        self._set_resource_utilization_defaults(uuid)
        vm_stats_timestamp = None
        vm_obj = InventoryCacheManager.get_object_from_cache(uuid,
                Constants.Vm)
        host_obj = InventoryCacheManager.get_object_from_cache(vm_obj.get_vmHostId(),
                Constants.VmHost)
        #Check if VM is in running state, else the performance data for that VM is not valid
        if vm_obj.get_powerState() == Constants.VM_POWER_STATES[1]:
            # Check if VM has old stats for sampling, else performance data is not sampled
            if LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                    Constants.OLD_STATS) is not None:
                vm_stats_timestamp = \
                    LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                        Constants.NEW_STATS).timestamp

                # Check the status of VM performance data collected, else the data is not valid
                if LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                        Constants.NEW_STATS).status == 0 \
                    and LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                        Constants.OLD_STATS).status == 0:
                    (pcentGuestCpu, guestCpus) = \
                        self._sample_cpu_stats(uuid)
                    (diskRead, diskWrite) = \
                        self._sample_disk_stats(uuid)
                    (netRead, netWrite) = self._sample_net_stats(uuid)
                    totalMemory = \
                        LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                            Constants.NEW_STATS).totalMemory
                    freeMemory = \
                        LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                            Constants.NEW_STATS).freeMemory
                    host_cpu_speed = host_obj.get_processorSpeedMhz()
                    self.resource_utilization.set_cpuUserLoad(pcentGuestCpu)
                    self.resource_utilization.set_ncpus(guestCpus)
                    self.resource_utilization.set_hostCpuSpeed(host_cpu_speed)
                    self.resource_utilization.set_hostMaxCpuSpeed(host_cpu_speed)
                    self.resource_utilization.set_diskRead(diskRead)
                    self.resource_utilization.set_diskWrite(diskWrite)
                    self.resource_utilization.set_netRead(netRead)
                    self.resource_utilization.set_netWrite(netWrite)
                    self.resource_utilization.set_totalMemory(totalMemory)
                    self.resource_utilization.set_configuredMemory(totalMemory)
                    self.resource_utilization.set_freeMemory(freeMemory)
                    self.resource_utilization.set_status(0)
                    self.resource_utilization.set_timestamp(datetime.datetime.utcfromtimestamp(vm_stats_timestamp))
                else:
                    LOG.error(_('Performance data of VM ' + uuid
                              + ' is not valid'))
                    self.resource_utilization.set_status(-1)
            else:
                LOG.error(_('Performance data of VM ' + uuid
                          + ' is not yet sampled'))
                self.resource_utilization.set_status(-1)
        else:
            LOG.info(_('VM ' + uuid + ' is not running'))
            self.resource_utilization.set_status(-1)
            LibvirtPerfMonitor.delete_perfdata_fromCache(uuid)

        self.resource_utilization.set_resourceId(uuid)
        self.resource_utilization.set_granularity(window_minutes)

        LOG.info(_('Exiting sample_vm_perfdata for VM ' + uuid))
        return self.resource_utilization

    def _set_resource_utilization_defaults(self, uuid):
        self.resource_utilization.set_cpuUserLoad(0.0)
        self.resource_utilization.set_ncpus(0)
        self.resource_utilization.set_hostCpuSpeed(0)
        self.resource_utilization.set_hostMaxCpuSpeed(0)
        self.resource_utilization.set_diskRead(0)
        self.resource_utilization.set_diskWrite(0)
        self.resource_utilization.set_netRead(0)
        self.resource_utilization.set_netWrite(0)
        self.resource_utilization.set_resourceId(uuid)
        self.resource_utilization.set_granularity(5)
        self.resource_utilization.set_totalMemory(0)
        self.resource_utilization.set_freeMemory(0)
        self.resource_utilization.set_configuredMemory(0)
        self.resource_utilization.set_timestamp(time.time())
        self.resource_utilization.set_status(-1)

    def _sample_cpu_stats(self, uuid):
        ''' cpu stats '''

        LOG.debug(_('Entering _sample_cpu_stats for uuid ' + uuid))
        prevcpuPerfTime = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.OLD_STATS).cpuPerfTime
        prevCpuTime = LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.OLD_STATS).cpuStats.cycles['user']

        cpuPerfTime = LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).cpuPerfTime
        cpuTime = LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).cpuStats.cycles['user']

        pcentbase = 0.0
        perftime_delta = self._get_delta(cpuPerfTime,
                prevcpuPerfTime)
        if perftime_delta > 0:
            pcentbase = self._get_delta(cpuTime, prevCpuTime) \
                * 100.0 / (perftime_delta * 1000.0 * 1000.0 * 1000.0)

        guestcpus = LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).ncpus
        LOG.debug(_('prevcpuPerfTime ' + str(prevcpuPerfTime)
                  + ' prevCpuTime ' + str(prevCpuTime) + ' cpuPerfTime '
                   + str(cpuPerfTime) + ' cpuTime ' + str(cpuTime)
                  + ' guestcpus ' + str(guestcpus)))

        pcentGuestCpu = pcentbase / int(guestcpus)
        LOG.debug(_('pcentGuestCpu ' + str(pcentGuestCpu)))

        pcentGuestCpu = max(0.0, min(100.0, pcentGuestCpu))

        LOG.debug(_('Exiting _sample_cpu_stats for uuid ' + uuid))
        return (pcentGuestCpu, int(guestcpus))

    def _sample_disk_stats(self, uuid):
        ''' disk stats '''

        LOG.debug(_('Entering _sample_disk_stats for uuid ' + uuid))
        prevdiskPerfTime = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.OLD_STATS).diskPerfTime
        prevdiskReadBytes = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.OLD_STATS).diskReadBytes
        prevdiskWriteBytes = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.OLD_STATS).diskWriteBytes

        diskPerfTime = LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).diskPerfTime
        diskReadBytes = LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).diskReadBytes
        diskWriteBytes = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).diskWriteBytes

        LOG.debug(_('prevdiskPerfTime ' + str(prevdiskPerfTime)
                  + ' prevdiskReadBytes ' + str(prevdiskReadBytes)
                  + ' prevdiskWriteBytes ' + str(prevdiskWriteBytes)))
        LOG.debug(_('diskPerfTime ' + str(diskPerfTime)
                  + ' diskReadBytes ' + str(diskReadBytes)
                  + ' diskWriteBytes ' + str(diskWriteBytes)))

        diskRead = \
            self._get_rate(self._get_delta(diskReadBytes,
                prevdiskReadBytes),
                self._get_delta(diskPerfTime,
                prevdiskPerfTime))
        diskWrite = \
            self._get_rate(self._get_delta(diskWriteBytes,
                prevdiskWriteBytes),
                self._get_delta(diskPerfTime,
                prevdiskPerfTime))

        LOG.debug(_('diskRead ' + str(diskRead) + ' diskWrite '
                  + str(diskWrite)))

        LOG.debug(_('Exiting _sample_disk_stats for uuid ' + uuid))
        return (diskRead, diskWrite)

    def _sample_net_stats(self, uuid):
        '''net stats'''

        LOG.debug(_('Entering _sample_net_stats for uuid ' + uuid))
        prevnetPerfTime = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.OLD_STATS).diskPerfTime
        prevnetReceivedBytes = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.OLD_STATS).netReceivedBytes
        prevnetTransmittedBytes = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.OLD_STATS).netTransmittedBytes

        netPerfTime = LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).diskPerfTime
        netReceivedBytes = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).netReceivedBytes
        netTransmittedBytes = \
            LibvirtPerfMonitor.get_perfdata_fromCache(uuid,
                Constants.NEW_STATS).netTransmittedBytes

        LOG.debug(_('prevnetPerfTime ' + str(prevnetPerfTime)
                  + ' prevnetReceivedBytes '
                  + str(prevnetReceivedBytes)
                  + ' prevnetTransmittedBytes '
                  + str(prevnetTransmittedBytes)))
        LOG.debug(_('netPerfTime ' + str(netPerfTime)
                  + ' netReceivedBytes ' + str(netReceivedBytes)
                  + ' netTransmittedBytes ' + str(netTransmittedBytes)))

        netRead = \
            self._get_rate(self._get_delta(netReceivedBytes,
                prevnetReceivedBytes),
                self._get_delta(netPerfTime, prevnetPerfTime))
        netWrite = \
            self._get_rate(self._get_delta(netTransmittedBytes,
                prevnetTransmittedBytes),
                self._get_delta(netPerfTime, prevnetPerfTime))

        LOG.debug(_('netRead ' + str(netRead) + ' netWrite '
                  + str(netWrite)))

        LOG.debug(_('Exiting _sample_net_stats for uuid ' + uuid))
        return (netRead, netWrite)

    def _get_delta(self, new_value, old_value):
        if new_value == 0:
            return 0

        res = float(new_value - old_value)
        if res < 0:
            res = 0
        return res

    def _get_rate(self, deltaBytes, deltaTime):
        if deltaTime > 0:
            rate = deltaBytes / deltaTime
        else:
            rate = 0.0

        return max(rate, 0, 0)  # avoid negative values at poweroff
