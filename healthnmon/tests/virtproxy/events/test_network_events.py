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

from healthnmon import test
from healthnmon.virtproxy.virt.libvirt.connection import LibvirtConnection
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    VirtualSwitch, PortGroup
from healthnmon.virtproxy.virt.libvirt.libvirt_inventorymonitor \
    import LibvirtNetwork
from healthnmon.tests import FakeLibvirt as libvirt
from healthnmon.constants import Constants
from nova.openstack.common.notifier import test_notifier
from healthnmon.notifier import api as notifier_api
from healthnmon.virtproxy.events import event_metadata
from healthnmon.virtproxy.inventory_manager import ComputeInventory
from healthnmon.virtproxy.inventory_cache_manager import InventoryCacheManager
from healthnmon.rmcontext import ComputeRMContext
import copy


class NetworkEventsTest(test.TestCase):

    def setUp(self):
        super(NetworkEventsTest, self).setUp()
        self.flags(hypervisor_type="fake")
        self.connection = LibvirtConnection(False)
        self.connection._wrapped_conn = libvirt.open("qemu:///system")
        rm_context = ComputeRMContext(
            rmType='QEMU', rmIpAddress='10.10.155.165',
            rmUserName='openstack',
            rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory()['1'] = \
            ComputeInventory(rm_context)
        self.libvirtNetwork = LibvirtNetwork(
            self.connection._wrapped_conn, '1')
        self.flags(healthnmon_notification_drivers=
                   ['nova.openstack.common.notifier.test_notifier'])
        test_notifier.NOTIFICATIONS = []

    def test_no_event_generated(self):
        vmhost = VmHost()
        vmhost.id = self.libvirtNetwork.compute_id
        self.libvirtNetwork._processNetworkEvents(None, vmhost)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 0)

    def test_network_added_event(self):
        cachedHost = VmHost()
        cachedHost.id = self.libvirtNetwork.compute_id
        vmhost = VmHost()
        vmhost.id = self.libvirtNetwork.compute_id
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        vmhost.set_virtualSwitches([vswitch])
        self.libvirtNetwork._processNetworkEvents(cachedHost, vmhost)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = event_metadata.get_EventMetaData(
            event_metadata.EVENT_TYPE_NETWORK_ADDED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'VirtualSwitch')
        self.assertEquals(payload['entity_id'], vswitch.get_id())

    def test_network_deleted_event(self):
        cachedHost = VmHost()
        cachedHost.id = self.libvirtNetwork.compute_id
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        cachedHost.set_virtualSwitches([vswitch])
        vmhost = copy.deepcopy(cachedHost)
        vmhost.get_virtualSwitches().pop()
        self.assertEquals(vmhost.get_virtualSwitches(), [])
        self.libvirtNetwork._processNetworkEvents(cachedHost, vmhost)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = event_metadata.get_EventMetaData(
            event_metadata.EVENT_TYPE_NETWORK_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'VirtualSwitch')
        self.assertEquals(payload['entity_id'], vswitch.get_id())

    def test_network_enabled_event(self):
        cachedHost = VmHost()
        cachedHost.id = self.libvirtNetwork.compute_id
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        vswitch.set_connectionState("Inactive")
        cachedHost.set_virtualSwitches([vswitch])
        vmhost = copy.deepcopy(cachedHost)
        vmhost.get_virtualSwitches()[0].set_connectionState("Active")
        self.libvirtNetwork._processNetworkEvents(cachedHost, vmhost)
        self.assertEquals(vmhost.get_virtualSwitches()[0].
                          get_connectionState(),
                          Constants.VIRSWITCH_STATE_ACTIVE)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = event_metadata.get_EventMetaData(
            event_metadata.EVENT_TYPE_NETWORK_ENABLED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'VirtualSwitch')
        self.assertEquals(payload['entity_id'], vswitch.get_id())
        self.assertEquals(payload["state"], 'Active')

    def test_network_disabled_event(self):
        cachedHost = VmHost()
        cachedHost.id = self.libvirtNetwork.compute_id
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        vswitch.set_connectionState("Active")
        cachedHost.set_virtualSwitches([vswitch])
        vmhost = copy.deepcopy(cachedHost)
        vmhost.get_virtualSwitches()[0].set_connectionState("Inactive")
        self.libvirtNetwork._processNetworkEvents(cachedHost, vmhost)
        self.assertEquals(vmhost.get_virtualSwitches()[0].
                          get_connectionState(),
                          Constants.VIRSWITCH_STATE_INACTIVE)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.WARN)
        event_type = event_metadata.get_EventMetaData(
            event_metadata.EVENT_TYPE_NETWORK_DISABLED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'VirtualSwitch')
        self.assertEquals(payload['entity_id'], vswitch.get_id())
        self.assertEquals(payload["state"], 'Inactive')

    def test_portGroup_added_event(self):
        cachedHost = VmHost()
        cachedHost.id = self.libvirtNetwork.compute_id
        vmhost = VmHost()
        vmhost.id = self.libvirtNetwork.compute_id
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        portGroup = PortGroup()
        portGroup.set_id("PortGroup_" + vswitch.get_id())
        portGroup.set_name(vswitch.get_name())
        portGroup.set_virtualSwitchId(vswitch.get_id())
        vswitch.set_portGroups([portGroup])
        vmhost.set_virtualSwitches([vswitch])
        vmhost.set_portGroups([portGroup])
        self.libvirtNetwork._processNetworkEvents(cachedHost, vmhost)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 2)
        msg = test_notifier.NOTIFICATIONS[1]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = event_metadata.get_EventMetaData(
            event_metadata.EVENT_TYPE_PORTGROUP_ADDED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'PortGroup')
        self.assertEquals(payload['entity_id'], portGroup.get_id())

    def test_portGroup_deleted_event(self):
        cachedHost = VmHost()
        cachedHost.id = self.libvirtNetwork.compute_id
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        portGroup = PortGroup()
        portGroup.set_id("PortGroup_" + vswitch.get_id())
        portGroup.set_name(vswitch.get_name())
        portGroup.set_virtualSwitchId(vswitch.get_id())
        vswitch.set_portGroups([portGroup])
        cachedHost.set_virtualSwitches([vswitch])
        cachedHost.set_portGroups([portGroup])
        vmhost = copy.deepcopy(cachedHost)
        vmhost.get_portGroups().pop()
        vmhost.get_virtualSwitches().pop()
        self.assertEquals(vmhost.get_virtualSwitches(), [])
        self.libvirtNetwork._processNetworkEvents(cachedHost, vmhost)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 2)
        msg = test_notifier.NOTIFICATIONS[1]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = event_metadata.get_EventMetaData(
            event_metadata.EVENT_TYPE_PORTGROUP_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'PortGroup')
        self.assertEquals(payload['entity_id'], portGroup.get_id())

    def test_PortGroup_Reconfigured_Event(self):
        cachedHost = VmHost()
        cachedHost.id = self.libvirtNetwork.compute_id
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        portGroup = PortGroup()
        portGroup.set_id("PortGroup_" + vswitch.get_id())
        portGroup.set_name(vswitch.get_name())
        portGroup.set_virtualSwitchId(vswitch.get_id())
        vswitch.set_portGroups([portGroup])
        cachedHost.set_virtualSwitches([vswitch])
        cachedHost.set_portGroups([portGroup])
        vmhost = copy.deepcopy(cachedHost)
        vmhost.get_portGroups()[0].set_name("vs11")
        vmhost.get_virtualSwitches()[0].set_name("vs11")
        vmhost.get_virtualSwitches()[0].get_portGroups()[0].set_name("vs11")
        self.libvirtNetwork._processNetworkEvents(cachedHost, vmhost)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = event_metadata.get_EventMetaData(
            event_metadata.EVENT_TYPE_PORTGROUP_RECONFIGURED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'PortGroup')
        self.assertEquals(payload['entity_id'], portGroup.get_id())
