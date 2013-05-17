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
from healthnmon.resourcemodel.healthnmonResourceModel import Vm
import mox
from healthnmon.virtproxy.events import api as events_api
from healthnmon.notifier import api as notifier_api
from healthnmon.virtproxy.events import event_metadata
from nova.db import api as nova_db
from nova.openstack.common.notifier import test_notifier


class APiTest(test.TestCase):

    ''' TestCase for healthnmon.notifier.api '''

    def setUp(self):
        super(APiTest, self).setUp()
        self.mox.StubOutWithMock(nova_db, 'service_get_all_by_topic')
        self.vm = Vm()
        self.vm.set_id('12345')
        self.vm.set_name('TestVm')
        self.flags(healthnmon_notification_drivers=[
            'nova.openstack.common.notifier.test_notifier'])
        test_notifier.NOTIFICATIONS = []

    def testNotify(self):

        scheduler_services = [{'host': 'testhost'}]

        nova_db. \
            service_get_all_by_topic(
                mox.IgnoreArg(),
                mox.IgnoreArg()).AndReturn(scheduler_services)
        self.mox.ReplayAll()
        self.assertEquals(events_api.notify(
            event_metadata.EVENT_TYPE_VM_DELETED,
            self.vm), None)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_VM_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        self.assertEquals(msg['publisher_id'],
                          'testhost.healthnmon')
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'],
                          self.vm.get_id())

    def testNotifyNoneScheduler(self):

        scheduler_services = None

        nova_db. \
            service_get_all_by_topic(
                mox.IgnoreArg(),
                mox.IgnoreArg()).AndReturn(scheduler_services)
        self.mox.ReplayAll()
        self.assertEquals(events_api.notify(
            event_metadata.EVENT_TYPE_VM_DELETED, self.vm), None)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_VM_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        self.assertEquals(msg['publisher_id'],
                          'healthnmon')
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'],
                          self.vm.get_id())

    def testNotifyEmptyScheduler(self):

        scheduler_services = []

        nova_db.service_get_all_by_topic(
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(scheduler_services)
        self.mox.ReplayAll()
        self.assertEquals(events_api.notify(
            event_metadata.EVENT_TYPE_VM_DELETED, self.vm), None)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_VM_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        self.assertEquals(msg['publisher_id'],
                          'healthnmon')
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'],
                          self.vm.get_id())

    def testNotifyMultipleScheduler(self):

        scheduler_services = [{'host': 'testhost'}, {'host': 'testhost2'
                                                     }]

        nova_db.service_get_all_by_topic(
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(scheduler_services)
        self.mox.ReplayAll()
        self.assertEquals(events_api.notify(
            event_metadata.EVENT_TYPE_VM_DELETED, self.vm), None)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_VM_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        self.assertEquals(msg['publisher_id'],
                          'testhost.healthnmon')
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'],
                          self.vm.get_id())

    def testNotifyNoneSchedulerHost(self):

        scheduler_services = [{'host': None}]

        nova_db.service_get_all_by_topic(
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(scheduler_services)
        self.mox.ReplayAll()
        self.assertEquals(events_api.notify(
            event_metadata.EVENT_TYPE_VM_DELETED, self.vm), None)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_VM_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        self.assertEquals(msg['publisher_id'],
                          'healthnmon')
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'],
                          self.vm.get_id())

    def testNotifyExceptionScheduler(self):
        nova_db.service_get_all_by_topic(mox.IgnoreArg(),
                                         mox.IgnoreArg()).AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertEquals(events_api.notify(
            event_metadata.EVENT_TYPE_VM_DELETED, self.vm), None)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = event_metadata.get_EventMetaData(
            event_metadata.EVENT_TYPE_VM_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        self.assertEquals(msg['publisher_id'],
                          'healthnmon')
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'],
                          self.vm.get_id())

    def tearDown(self):
        super(APiTest, self).tearDown()
