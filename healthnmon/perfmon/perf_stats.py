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

""" Defines performance statistics required for sampling performance data for specified period """


class Stats(object):

    """ Represents performance data at a certain point in time """

    def __init__(self):
        self.__timestamp = None
        self.__cpuPerfTime = None
        self.__diskPerfTime = None
        self.__netPerfTime = None
        self.__totalMemory = None
        self.__freeMemory = None
        self.__configuredMemory = None
        self.__diskReadBytes = None
        self.__diskWriteBytes = None
        self.__netReceivedBytes = None
        self.__netTransmittedBytes = None
        self.__cpuStats = CPUStats()
        self.__ncpus = None
        self.__status = 0

    def get_status(self):
        return self.__status

    def set_status(self, value):
        self.__status = value

    def get_timestamp(self):
        return self.__timestamp

    def set_timestamp(self, value):
        self.__timestamp = value

    def get_cpu_perf_time(self):
        return self.__cpuPerfTime

    def get_disk_perf_time(self):
        return self.__diskPerfTime

    def get_net_perf_time(self):
        return self.__netPerfTime

    def get_total_memory(self):
        return self.__totalMemory

    def get_free_memory(self):
        return self.__freeMemory

    def get_configured_memory(self):
        return self.__configuredMemory

    def get_disk_read_bytes(self):
        return self.__diskReadBytes

    def get_disk_write_bytes(self):
        return self.__diskWriteBytes

    def get_net_received_bytes(self):
        return self.__netReceivedBytes

    def get_net_transmitted_bytes(self):
        return self.__netTransmittedBytes

    def get_cpu_stats(self):
        return self.__cpuStats

    def get_ncpus(self):
        return self.__ncpus

    def set_cpu_perf_time(self, value):
        self.__cpuPerfTime = value

    def set_disk_perf_time(self, value):
        self.__diskPerfTime = value

    def set_net_perf_time(self, value):
        self.__netPerfTime = value

    def set_total_memory(self, value):
        self.__totalMemory = value

    def set_free_memory(self, value):
        self.__freeMemory = value

    def set_configured_memory(self, value):
        self.__configuredMemory = value

    def set_disk_read_bytes(self, value):
        self.__diskReadBytes = value

    def set_disk_write_bytes(self, value):
        self.__diskWriteBytes = value

    def set_net_received_bytes(self, value):
        self.__netReceivedBytes = value

    def set_net_transmitted_bytes(self, value):
        self.__netTransmittedBytes = value

    def set_cpu_stats(self, value):
        self.__cpuStats = value

    def set_ncpus(self, value):
        self.__ncpus = value

    cpuPerfTime = property(get_cpu_perf_time, set_cpu_perf_time, None,
                           None)
    diskPerfTime = property(get_disk_perf_time, set_disk_perf_time,
                            None, None)
    netPerfTime = property(get_net_perf_time, set_net_perf_time, None,
                           None)
    totalMemory = property(get_total_memory, set_total_memory, None,
                           None)
    freeMemory = property(get_free_memory, set_free_memory, None, None)
    configuredMemory = property(get_configured_memory,
                                set_configured_memory, None, None)
    diskReadBytes = property(get_disk_read_bytes, set_disk_read_bytes,
                             None, None)
    diskWriteBytes = property(get_disk_write_bytes,
                              set_disk_write_bytes, None, None)
    netReceivedBytes = property(get_net_received_bytes,
                                set_net_received_bytes, None, None)
    netTransmittedBytes = property(get_net_transmitted_bytes,
                                   set_net_transmitted_bytes, None,
                                   None)
    cpuStats = property(get_cpu_stats, set_cpu_stats, None, None)
    ncpus = property(get_ncpus, set_ncpus, None, None)
    timestamp = property(get_timestamp, set_timestamp, None, None)
    status = property(get_status, set_status, None, None)


class CPUStats(object):

    """ Represents CPU performance data"""

    def __init__(self):
        self.__total = None
        self.__cycles = {
            'user: ': None,
            'system': None,
            'idle': None,
            'total': None,
        }

    def get_cycles(self):
        return self.__cycles

    def set_cycles(self, value):
        self.__cycles = value

    cycles = property(get_cycles, set_cycles, None, None)
