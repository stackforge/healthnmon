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
Created on Mar 7, 2012

@author: root
'''

import unittest
from healthnmon.perfmon import perf_stats


class StatsTestCase(unittest.TestCase):

    def setUp(self):
        self.perfstats = perf_stats.Stats()

    def test_timestamp(self):
        self.perfstats.timestamp = '4'
        self.assertEquals(self.perfstats.timestamp, '4')

    def test_cpuPerfTime(self):
        self.perfstats.cpuPerfTime = '20'
        self.assertEquals(self.perfstats.cpuPerfTime, '20')

    def test_diskPerfTime(self):
        self.perfstats.diskPerfTime = '40'
        self.assertEquals(self.perfstats.diskPerfTime, '40')

    def test_netPerfTime(self):
        self.perfstats.netPerfTime = '85'
        self.assertEquals(self.perfstats.netPerfTime, '85')

    def test_totalMemory(self):
        self.perfstats.totalMemory = '1024'
        self.assertEquals(self.perfstats.totalMemory, '1024')

    def test_freeMemory(self):
        self.perfstats.freeMemory = '1024'
        self.assertEquals(self.perfstats.freeMemory, '1024')

    def test_configuredMemory(self):
        self.perfstats.configuredMemory = '1024'
        self.assertEquals(self.perfstats.configuredMemory, '1024')

    def test_diskReadBytes(self):
        self.perfstats.diskReadBytes = '1024'
        self.assertEquals(self.perfstats.diskReadBytes, '1024')

    def test_diskWriteBytes(self):
        self.perfstats.diskWriteBytes = '1024'
        self.assertEquals(self.perfstats.diskWriteBytes, '1024')

    def test_netReceivedBytes(self):
        self.perfstats.netReceivedBytes = '1024'
        self.assertEquals(self.perfstats.netReceivedBytes, '1024')

    def test_netTransmittedBytes(self):
        self.perfstats.netTransmittedBytes = '1024'
        self.assertEquals(self.perfstats.netTransmittedBytes, '1024')

    def test_cpuStats(self):
        self.perfstats.cpuStats = perf_stats.CPUStats()
        self.assertTrue(isinstance(self.perfstats.cpuStats,
                        perf_stats.CPUStats))
        cycles_dict = {
            'user': '3',
            'system': '4',
            'idle': '3',
            'total': '10',
            }

        # self.perfstats.cpuStats.set_cycles(cycles_dict)

        self.perfstats.cpuStats.cycles = cycles_dict
        self.assertEquals(self.perfstats.cpuStats.cycles, cycles_dict)

    def test_ncpus(self):
        self.perfstats.ncpus = '4'
        self.assertEquals(self.perfstats.ncpus, '4')

    def test_status(self):
        self.perfstats.status = 1
        self.assertEquals(self.perfstats.status, 1)
