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
A fake (in-memory) hypervisor+api.

Allows nova testing w/o a hypervisor.  This module also documents the
semantics of real hypervisor connections.

"""

from healthnmon.virt import driver
from healthnmon import log as logging

LOG = logging.getLogger('healthnmon.virt.fake')


def get_connection(_=None):

    # The read_only parameter is ignored.

    return FakeConnection.instance()


class FakeConnection(driver.ComputeInventoryDriver):

    """Fake hypervisor driver"""

    def __init__(self):
        self.instances = {}
        self.host_status = {
            'host_name-description': 'Fake Host',
            'host_hostname': 'fake-mini',
            'host_memory_total': 8000000000,
            'host_memory_overhead': 10000000,
            'host_memory_free': 7900000000,
            'host_memory_free_computed': 7900000000,
            'host_other_config': {},
            'host_ip_address': '192.168.1.109',
            'host_cpu_info': {},
            'disk_available': 500000000000,
            'disk_total': 600000000000,
            'disk_used': 100000000000,
            'host_uuid': 'cedb9b39-9388-41df-8891-c5c9a0c0fe5f',
            'host_name_label': 'fake-mini',
            }
        self._mounts = {}

    @classmethod
    def instance(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    '''def init_host(self, rmcontext):
        return'''

    '''@staticmethod
    def get_host_ip_addr():
        return '192.168.0.1'''

    def init_rmcontext(self, compute_rmcontext):
        pass

    '''def update_inventory(self):
        pass'''

    @property
    def uri(self):
        return "fake:///system"

    def get_new_connection(self, uri, read_only):
        import healthnmon.tests.FakeLibvirt as FakeLibvirt
        return FakeLibvirt.openReadOnly(uri)

    def update_perfdata(self, uuid, perfmon_type):
        pass

    def get_resource_utilization(
        self,
        uuid,
        perfmon_type,
        window_minutes,
        ):
        pass
