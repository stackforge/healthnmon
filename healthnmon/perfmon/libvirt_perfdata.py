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

"""Module responsible for collecting performance data
of KVM Host andVm from libvirt"""

from healthnmon.resourcemodel.healthnmonResourceModel \
    import ResourceUtilization
from healthnmon.utils import XMLUtils
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.events import api as event_api
from healthnmon.events import event_metadata
from healthnmon.constants import Constants
from healthnmon.perfmon.perf_stats import Stats
from healthnmon import log
from nova.openstack.common import cfg
import time
import datetime


CONF = cfg.CONF
LOG = log.getLogger('healthnmon.libvirt_perfdata')

libvirt = None


class LibvirtPerfMonitor:
    """ Class responsible for invoking refresh and sample of KVM Host \
    utilization data using libvirt """

    perfDataCache = {}

    @staticmethod
    def get_perfdata_fromCache(uuid, stats_type):
        if uuid in LibvirtPerfMonitor.perfDataCache:
            return LibvirtPerfMonitor.perfDataCache[uuid][stats_type]

    @staticmethod
    def update_perfdata_InCache(uuid, old_stats, new_stats):
        if uuid in LibvirtPerfMonitor.perfDataCache:
            LibvirtPerfMonitor.perfDataCache[uuid][Constants.OLD_STATS] = \
                old_stats
            LibvirtPerfMonitor.perfDataCache[uuid][Constants.NEW_STATS] = \
                new_stats

    @staticmethod
    def delete_perfdata_fromCache(uuid):
        if uuid in LibvirtPerfMonitor.perfDataCache:
            del LibvirtPerfMonitor.perfDataCache[uuid]

    def __init__(self):
        global libvirt
        if libvirt is None:
            libvirt = __import__('libvirt')

    def refresh_perfdata(
        self,
        conn,
        uuid,
        perfmon_type,
    ):
        '''Refreshes the performance data  '''

        if uuid not in LibvirtPerfMonitor.perfDataCache:
            LibvirtPerfMonitor.perfDataCache[uuid] = \
                {Constants.OLD_STATS: None, Constants.NEW_STATS: None}

        if perfmon_type == Constants.VmHost:
            LibvirtVmHostPerfData(conn, uuid).refresh_perfdata()
            host_obj = InventoryCacheManager.get_object_from_cache(
                uuid,
                Constants.VmHost)
            if host_obj is not None:
                event_api.notify_host_update(
                    event_metadata.EVENT_TYPE_HOST_UPDATED, host_obj)
        elif perfmon_type == Constants.Vm:
            LibvirtVmPerfData(conn, uuid).refresh_perfdata()

    def get_resource_utilization(
        self,
        uuid,
        perfmon_type,
        window_minutes,
    ):
        '''Returns the sampled utilization data of KVM host '''

        if perfmon_type == Constants.VmHost:
            return SamplePerfData().sample_host_perfdata(uuid,
                                                         window_minutes)
        elif perfmon_type == Constants.Vm:
            return SamplePerfData().sample_vm_perfdata(uuid,
                                                       window_minutes)


class LibvirtVmHostPerfData:

    """ Responsible for collecting KVM VM Host
    Performance data from libvirt """

    def __init__(self, conn, uuid):
        self.libvirtconn = conn
        self.uuid = uuid
        self.old_stats = None
        self.new_stats = None
        self.temp_stats = Stats()
        self.utils = XMLUtils()

    def refresh_perfdata(self):
        """ Responsible for refreshing Memory statistics of KVM Vm Host"""

        LOG.info(_('Entering refresh_perfdata for vm host  '
                   + self.uuid))
        self.old_stats = \
            LibvirtPerfMonitor.get_perfdata_fromCache(self.uuid,
                                                      Constants.OLD_STATS)
        self.new_stats = \
            LibvirtPerfMonitor.get_perfdata_fromCache(self.uuid,
                                                      Constants.NEW_STATS)

        self._update_cpu_stats()
        self._update_memory_stats()

        self.temp_stats.timestamp = time.time()
        self.old_stats = self.new_stats
        self.new_stats = self.temp_stats

        LibvirtPerfMonitor.update_perfdata_InCache(
            self.uuid,
            self.old_stats, self.new_stats)
        LOG.info(_('refreshed utilization data for host ' + self.uuid))
        LOG.info(_('Exiting refresh perfdata for host '
                   + self.uuid))

    def _update_cpu_stats(self):
        global libvirt
        try:
            cpustats = self.libvirtconn.getCPUStats(
                libvirt.VIR_NODE_CPU_STATS_ALL_CPUS, 0)
            self.temp_stats.cpuStats.cycles['user'] = cpustats['user']
            self.temp_stats.cpuStats.cycles['system'] = cpustats['kernel']
            self.temp_stats.cpuPerfTime = time.time()
            self.temp_stats.ncpus = self.libvirtconn.getInfo()[2]
            LOG.debug(_('cpu stats of host ' + self.uuid + ' : userLoad : \
            ' + str(self.temp_stats.cpuStats.cycles['user'])
                + ', ncpus: ' + str(self.temp_stats.ncpus)))
        except Exception, err:
            LOG.error(_("Error reading cpu stats for host %s: %s"
                        % (self.uuid, err)))
            self.temp_stats.status = -1

    def _update_memory_stats(self):
        global libvirt
        try:
            memstats = self.libvirtconn.getMemoryStats(
                libvirt.VIR_NODE_MEMORY_STATS_ALL_CELLS, 0)
            self.temp_stats.totalMemory = memstats['total']
            self.temp_stats.freeMemory = memstats[
                'free'] + memstats['buffers'] + memstats['cached']
            LOG.debug(_('memory stats of host ' + self.uuid + ' : \
            totalMemory:\
             ' + str(self.temp_stats.totalMemory)
                + ', Free Memory: \
             ' + str(self.temp_stats.freeMemory)))
        except Exception, err:
            LOG.error(_("Error reading memory stats for host %s: %s"
                        % (self.uuid, err)))
            self.temp_stats.status = -1


class LibvirtVmPerfData:

    """ Responsible for collecting KVM VM Performance data from libvirt """

    def __init__(self, conn, uuid):
        self.libvirtconn = conn
        self.uuid = uuid
        self.domainObj = None
        self.old_stats = None
        self.new_stats = None
        self.temp_stats = Stats()
        self.utils = XMLUtils()

    def refresh_perfdata(self):
        """ Responsible for refreshing CPU,Disk,Network,
        Memory statistics of KVM Vm """

        self.domainObj = self.libvirtconn.lookupByUUIDString(self.uuid)
        LOG.info(_('Entering refresh_perfdata for vm '
                   + self.uuid))

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
                        % (self.uuid, err)))

        if info is not None and vmXML is not None:
            self._update_cpu_stats(info, vmXML)
            self._update_disk_stats(vmXML)
            self._update_net_stats(vmXML)
            self._update_memory_stats(vmXML)
        else:
            LOG.error(_("Error reading CPU,disk, net stats for '%s'"
                      % self.uuid))
            self.temp_stats.status = -1

        self.temp_stats.timestamp = time.time()
        self.old_stats = self.new_stats
        self.new_stats = self.temp_stats

        LibvirtPerfMonitor.update_perfdata_InCache(
            self.uuid,
            self.old_stats, self.new_stats)
        LOG.info(_('refreshed utilization data for vm ' + self.uuid))
        LOG.info(_('Exiting refresh perfdata for VM '
                   + self.uuid))

    def _update_cpu_stats(self, domain_info, vmXML):
        self.temp_stats.cpuStats.cycles['user'] = domain_info[4]
        self.temp_stats.cpuPerfTime = time.time()
        self.temp_stats.ncpus = self.utils.parseXML(vmXML, "//domain/vcpu")

        LOG.debug(_('cpu stats of VM ' + self.uuid + ' : userLoad : ' +
                    str(self.temp_stats.cpuStats.cycles['user'])
                    + ', ncpus: ' + str(self.temp_stats.ncpus)))

    def _update_disk_stats(self, vmXML):
        rd = 0
        wr = 0

        disksAttached = self.utils.getNodeXML(
            vmXML,
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
                LOG.error(_("Error reading disk stats for '%s' for disk \
                '%s': %s"
                            % (self.uuid, dev, err)))
                self.temp_stats.status = -1
                break

        self.temp_stats.diskReadBytes = rd
        self.temp_stats.diskWriteBytes = wr
        self.temp_stats.diskPerfTime = time.time()
        LOG.debug(_('disk stats of vm ' + self.uuid + ' : rd: ' +
                    str(self.temp_stats.netReceivedBytes)
                    + ', wr: ' +
                    str(self.temp_stats.netTransmittedBytes)))

    def _update_net_stats(self, vmXML):
        rx = 0
        tx = 0

        vmNetAdapterAttached = self.utils.getNodeXML(
            vmXML,
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
                LOG.error(_("Error reading net stats for '%s' for interface '\
                %s': %s"
                            % (self.uuid, dev, err)))
                self.temp_stats.status = -1
                break

        self.temp_stats.netReceivedBytes = rx
        self.temp_stats.netTransmittedBytes = tx
        self.temp_stats.netPerfTime = time.time()
        LOG.debug(_('network stats of vm ' + self.uuid + ' : rx: ' +
                    str(self.temp_stats.netReceivedBytes)
                    + ', tx: ' + str(self.temp_stats.netTransmittedBytes)))

    def _update_memory_stats(self, vmXML):
        total_memory = long(self.utils.parseXML(vmXML, '//domain/memory'
                                                ))
        memory_consumed = long(self.utils.parseXML(vmXML,
                               '//domain/currentMemory'))

        self.temp_stats.totalMemory = total_memory
        self.temp_stats.freeMemory = total_memory - memory_consumed

        LOG.debug(_('memory stats of vm ' + self.uuid + ' : totalMemory: '
                    + str(self.temp_stats.totalMemory)
                    + ', Free Memory: '
                    + str(self.temp_stats.freeMemory)))


class SamplePerfData:
    """ Class responsible for sampling KVM Host utilization data for
        specified window minutes """

    def __init__(self):
        self.resource_utilization = None

    def sample_host_perfdata(self, uuid, window_minutes):
        LOG.info(_('Entering sampling utilization data for host '
                   + uuid))

        self.resource_utilization = ResourceUtilization()
        self._set_resource_utilization_defaults(uuid)
        self.timestamp = time.time()

        host_obj = InventoryCacheManager.get_object_from_cache(
            uuid, Constants.VmHost)
        self.old_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
            uuid, Constants.OLD_STATS)
        self.new_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
            uuid, Constants.NEW_STATS)

        if host_obj.get_connectionState() == Constants.VMHOST_DISCONNECTED:
            LOG.error(_('host ' + uuid + ' is disconnected'))
            return self.resource_utilization

        # Check if host has old stats for sampling, else utilization data is
        # not sampled
        if self.old_stats is not None:
            # Check the status of host utilization data collected, else the
            # data is not valid
            if self.new_stats.status == 0 and self.old_stats.status == 0:
                (pcentUserCpu, pcentSystemCpu,
                 host_cpus) = self._sample_cpu_stats(uuid)
                host_cpu_speed = host_obj.get_processorSpeedMhz()
                totalMemory = self.new_stats.totalMemory
                freeMemory = self.new_stats.freeMemory

                self.resource_utilization.set_cpuUserLoad(pcentUserCpu)
                self.resource_utilization.set_cpuSystemLoad(pcentSystemCpu)
                self.resource_utilization.set_ncpus(host_cpus)
                self.resource_utilization.set_hostCpuSpeed(host_cpu_speed)
                self.resource_utilization.set_hostMaxCpuSpeed(host_cpu_speed)
                self.resource_utilization.set_totalMemory(totalMemory)
                self.resource_utilization.set_freeMemory(freeMemory)
                self.resource_utilization.set_configuredMemory(totalMemory)
                self.resource_utilization.set_resourceId(uuid)
                self.resource_utilization.set_granularity(window_minutes)
                self.resource_utilization.set_status(0)
                self.resource_utilization.set_timestamp(
                    datetime.datetime.utcfromtimestamp(
                        self.new_stats.timestamp))
                LOG.info(_('sampled cpu/memory utilization data for host ' +
                         uuid + ' for window minutes ' + str(window_minutes)))
            else:
                LOG.error(_(
                    'utilization data of host ' + uuid + ' is not valid'))
        else:
            LOG.error(_(
                'utilization data of host ' + uuid + ' is not yet sampled'))

        # sample disk/network data only if sampling of cpu/memory is successful
        if self.resource_utilization.get_status() == 0:
            diskRead = 0
            diskWrite = 0
            netRead = 0
            netWrite = 0
            LOG.debug(_(
                'aggregating disk/network utilization data using vms data for \
                host ' + uuid))
            # disk/network utilization data is calculated aggregating the
            # performance data of VM's
            for vm_id in host_obj.get_virtualMachineIds():
                vm_obj = InventoryCacheManager.get_object_from_cache(
                    vm_id, Constants.Vm)
                # Check if VM is in running state, else skip the utilization
                # data for that VM
                if vm_obj.get_powerState() == Constants.VM_POWER_STATES[1]:
                    vm_old_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
                        vm_id, Constants.OLD_STATS)
                    vm_new_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
                        vm_id, Constants.NEW_STATS)
                    # Check if VM has old stats for sampling, else utilization
                    # data is not valid
                    if vm_old_stats is not None:
                        LOG.debug(_('time now :' + str(
                            self.timestamp) + ' last sampled time:' +
                            str(vm_new_stats.timestamp)))

                        # Check if the VM utilization data is collected in \
                        # last 5 minutes(considering buffer of 1 minute) and
                        # status of the VM utilization data, else performance
                        # data for VM is stale and is not valid
                        diff = self.timestamp - vm_new_stats.timestamp
                        if diff < CONF.perfmon_refresh_interval + 60 \
                                and vm_new_stats.status == 0:
                            (vmdiskRead, vmdiskWrite) = \
                                self._sample_disk_stats(
                                    vm_id)
                            (vmnetRead, vmnetWrite) = self._sample_net_stats(
                                vm_id)
                            diskRead += vmdiskRead
                            diskWrite += vmdiskWrite
                            netRead += vmnetRead
                            netWrite += vmnetWrite
                        else:
                            LOG.error(_(
                                'disk/network utilization data of vm \
                            ' + vm_id + ' on host ' + uuid + ' is not valid'))
                            break
                    else:
                        LOG.error(_('disk/network utilization data of vm ' +
                                  vm_id + ' on host ' + uuid + ' is \
                                  not yet sampled'))
                        break
                else:
                    LOG.info(_('vm ' + vm_id + ' on host ' + uuid +
                             ' is not active. skipping disk/network \
                             utilization data of vm '))

            self.resource_utilization.set_diskRead(diskRead)
            self.resource_utilization.set_diskWrite(diskWrite)
            self.resource_utilization.set_netRead(netRead)
            self.resource_utilization.set_netWrite(netWrite)
            LOG.info(_('sampled disk/network utilization data for host ' +
                     uuid + ' for window minutes ' + str(window_minutes)))

        LOG.info(_('Exiting sampling utilization data for host ' + uuid))
        return self.resource_utilization

    def sample_vm_perfdata(self, uuid, window_minutes):
        LOG.info(_('Entering sampling utilization data for vm  ' + uuid))

        self.resource_utilization = ResourceUtilization()
        self._set_resource_utilization_defaults(uuid)

        vm_obj = InventoryCacheManager.get_object_from_cache(
            uuid, Constants.Vm)
        host_obj = InventoryCacheManager.get_object_from_cache(
            vm_obj.get_vmHostId(), Constants.VmHost)
        self.old_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
            uuid, Constants.OLD_STATS)
        self.new_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
            uuid, Constants.NEW_STATS)

        # Check if VM is in running state, else the utilization data for that
        # VM is not valid
        if vm_obj.get_powerState() == Constants.VM_POWER_STATES[1]:
            # Check if VM has old stats for sampling, else utilization data is
            # not sampled
            if self.old_stats is not None:
                # Check the status of VM utilization data collected, else the
                # data is not valid
                if self.new_stats.status == 0 and self.old_stats.status == 0:
                    (pcentUserCpu, pcentSystemCpu,
                     guestCpus) = self._sample_cpu_stats(uuid)
                    (diskRead, diskWrite) = self._sample_disk_stats(uuid)
                    (netRead, netWrite) = self._sample_net_stats(uuid)
                    totalMemory = self.new_stats.totalMemory
                    freeMemory = self.new_stats.freeMemory
                    host_cpu_speed = host_obj.get_processorSpeedMhz()

                    self.resource_utilization.set_cpuUserLoad(pcentUserCpu)
                    self.resource_utilization.set_cpuSystemLoad(pcentSystemCpu)
                    self.resource_utilization.set_ncpus(guestCpus)
                    self.resource_utilization.set_hostCpuSpeed(host_cpu_speed)
                    self.resource_utilization.set_hostMaxCpuSpeed(
                        host_cpu_speed)
                    self.resource_utilization.set_diskRead(diskRead)
                    self.resource_utilization.set_diskWrite(diskWrite)
                    self.resource_utilization.set_netRead(netRead)
                    self.resource_utilization.set_netWrite(netWrite)
                    self.resource_utilization.set_totalMemory(totalMemory)
                    self.resource_utilization.set_configuredMemory(totalMemory)
                    self.resource_utilization.set_freeMemory(freeMemory)
                    self.resource_utilization.set_status(0)
                    self.resource_utilization.set_timestamp(
                        datetime.datetime.utcfromtimestamp
                        (self.new_stats.timestamp))
                    LOG.info(_('sampled utilization data for vm ' +
                             uuid + ' for window minutes '
                             + str(window_minutes)))
                else:
                    LOG.error(_(
                        'utilization data of vm ' + uuid + ' is not valid'))
            else:
                LOG.error(_(
                    'utilization data of vm ' + uuid + ' is not yet sampled'))
        else:
            LOG.error(_('vm ' + uuid + ' is not active'))
            LibvirtPerfMonitor.delete_perfdata_fromCache(uuid)

        self.resource_utilization.set_resourceId(uuid)
        self.resource_utilization.set_granularity(window_minutes)

        LOG.info(_('Exiting sample utilization data for vm ' + uuid))
        return self.resource_utilization

    def _set_resource_utilization_defaults(self, uuid):
        self.resource_utilization.set_cpuUserLoad(0.0)
        self.resource_utilization.set_cpuSystemLoad(0.0)
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
        ''' sample cpu stats for given window minutes'''

        prevcpuPerfTime = self.old_stats.cpuPerfTime
        prevCpuUserTime = self.old_stats.cpuStats.cycles['user']
        prevCpuSystemTime = self.old_stats.cpuStats.cycles['system']

        cpuPerfTime = self.new_stats.cpuPerfTime
        cpuUserTime = self.new_stats.cpuStats.cycles['user']
        cpuSystemTime = self.new_stats.cpuStats.cycles['system']

        pcentUserbase = 0.0
        pcentSystembase = 0.0
        pcentUserCpu = 0.0
        pcentSystemCpu = 0.0

        # cpu user and kernel time is obtained in nano seconds and time \
        # delta is in seconds
        # Hence dividing the delta of cpu time by 10 pow 9
        perftime_delta = self._get_delta(cpuPerfTime, prevcpuPerfTime)
        cpus = self.new_stats.ncpus
        if perftime_delta > 0:
            pcentUserbase = self._get_delta(cpuUserTime, prevCpuUserTime)\
                * 100.0 / (
                    perftime_delta * 1000.0 * 1000.0 * 1000.0)
            pcentUserCpu = pcentUserbase / int(cpus)
            pcentUserCpu = max(0.0, min(100.0, pcentUserCpu))

            if (cpuSystemTime > 0):
                pcentSystembase = self._get_delta(
                    cpuSystemTime, prevCpuSystemTime) * 100.0 / (
                        perftime_delta * 1000.0 * 1000.0 * 1000.0)
                pcentSystemCpu = pcentSystembase / int(cpus)
                pcentSystemCpu = max(0.0, min(100.0, pcentSystemCpu))

        LOG.debug(_('pcentUserCpu ' + str(pcentUserCpu) + ' \
        pcentSystemCpu ' + str(
            pcentSystemCpu) + ' cpus ' + str(cpus)))
        return (pcentUserCpu, pcentSystemCpu, int(cpus))

    def _sample_disk_stats(self, uuid):
        ''' sample disk stats for given window minutes '''

        old_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
            uuid, Constants.OLD_STATS)
        new_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
            uuid, Constants.NEW_STATS)

        prevdiskPerfTime = old_stats.diskPerfTime
        prevdiskReadBytes = old_stats.diskReadBytes
        prevdiskWriteBytes = old_stats.diskWriteBytes

        diskPerfTime = new_stats.diskPerfTime
        diskReadBytes = new_stats.diskReadBytes
        diskWriteBytes = new_stats.diskWriteBytes

        LOG.debug(_('prevdiskPerfTime ' + str(prevdiskPerfTime) + ' \
        prevdiskReadBytes ' + str(prevdiskReadBytes)
                  + ' prevdiskWriteBytes ' + str(prevdiskWriteBytes)))

        LOG.debug(_('diskPerfTime ' + str(diskPerfTime) + ' diskReadBytes \
        ' + str(diskReadBytes)
            + ' diskWriteBytes ' + str(diskWriteBytes)))

        diskRead = self._get_rate(self._get_delta(
            diskReadBytes, prevdiskReadBytes),
            self._get_delta(
                diskPerfTime, prevdiskPerfTime))
        diskWrite = self._get_rate(self._get_delta(
            diskWriteBytes, prevdiskWriteBytes),
            self._get_delta(diskPerfTime,
                            prevdiskPerfTime))

        LOG.debug(_('diskRead ' + str(
            diskRead) + ' diskWrite ' + str(diskWrite)))

        return (diskRead, diskWrite)

    def _sample_net_stats(self, uuid):
        '''sample network stats for given window minutes'''

        old_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
            uuid, Constants.OLD_STATS)
        new_stats = LibvirtPerfMonitor.get_perfdata_fromCache(
            uuid, Constants.NEW_STATS)

        prevnetPerfTime = old_stats.diskPerfTime
        prevnetReceivedBytes = old_stats.netReceivedBytes
        prevnetTransmittedBytes = old_stats.netTransmittedBytes

        netPerfTime = new_stats.diskPerfTime
        netReceivedBytes = new_stats.netReceivedBytes
        netTransmittedBytes = new_stats.netTransmittedBytes

        LOG.debug(_('prevnetPerfTime ' + str(prevnetPerfTime) + ' \
        prevnetReceivedBytes ' + str(prevnetReceivedBytes)
                  + ' prevnetTransmittedBytes ' +
                  str(prevnetTransmittedBytes)))
        LOG.debug(_('netPerfTime ' + str(netPerfTime) + '\
         netReceivedBytes ' + str(netReceivedBytes)
                  + ' netTransmittedBytes ' + str(netTransmittedBytes)))

        netRead = self._get_rate(self._get_delta(
            netReceivedBytes, prevnetReceivedBytes),
            self._get_delta(netPerfTime, prevnetPerfTime))
        netWrite = self._get_rate(self._get_delta(
            netTransmittedBytes, prevnetTransmittedBytes),
            self._get_delta(netPerfTime, prevnetPerfTime))

        LOG.debug(_('netRead ' + str(netRead) + ' netWrite ' + str(netWrite)))

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
