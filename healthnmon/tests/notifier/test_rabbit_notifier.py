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

from nova import test
import mox
from nova.openstack.common import rpc
import healthnmon.notifier.rabbit_notifier
from nova.openstack.common import context


class RabbitNotifierTest(test.TestCase):

    ''' TestCase for healthnmon.notifier.rabbit_notifier '''
    def setUp(self):
        self.flags(healthnmon_default_notification_level='INFO')
        super(RabbitNotifierTest, self).setUp()
        self.mox.StubOutWithMock(rpc, 'notify')
        self.context = context.get_admin_context()

    def testNotify(self):
        message = {
            'priority': 'INFO',
            'event_type': 'LifeCycle.Vm.Reconfigured',
            'payload': {'entity_id': '024c1520-f836-47f7-3c91-df627096f8ab'},
            'message_id': '409e109d-41c0-4b75-9019-04aa3329c67b',
            }

        rpc.notify(mox.IgnoreArg(), 'healthnmon_notification',
                 mox.IgnoreArg()).AndReturn(None)
        self.mox.ReplayAll()
        self.assertEquals(healthnmon.notifier.rabbit_notifier.notify(self.context, message),
                          None)

    def testNotifyEvent_TypeNone(self):
        message = {
            'priority': 'INFO',
            'event_type': None,
            'payload': {'entity_id': '024c1520-f836-47f7-3c91-df627096f8ab'},
            'message_id': '409e109d-41c0-4b75-9019-04aa3329c67b',
            }

        rpc.notify(mox.IgnoreArg(), 'healthnmon_notification',
                 mox.IgnoreArg()).AndReturn(None)
        self.mox.ReplayAll()
        self.assertEquals(healthnmon.notifier.rabbit_notifier.notify(self.context, message),
                          None)

    def testNotifyPayloadNone(self):
        message = {
            'priority': 'INFO',
            'event_type': 'LifeCycle.Vm.Reconfigured',
            'payload': None,
            'message_id': '409e109d-41c0-4b75-9019-04aa3329c67b',
            }

        rpc.notify(mox.IgnoreArg(), 'healthnmon_notification',
                 mox.IgnoreArg()).AndReturn(None)
        self.mox.ReplayAll()
        self.assertEquals(healthnmon.notifier.rabbit_notifier.notify(self.context, message),
                          None)

    def testNotifyEntity_IdNone(self):
        message = {
            'priority': 'INFO',
            'event_type': 'LifeCycle.Vm.Reconfigured',
            'payload': {'entity_id': None},
            'message_id': '409e109d-41c0-4b75-9019-04aa3329c67b',
            }

        rpc.notify(mox.IgnoreArg(), 'healthnmon_notification',
                 mox.IgnoreArg()).AndReturn(None)
        self.mox.ReplayAll()
        self.assertEquals(healthnmon.notifier.rabbit_notifier.notify(self.context, message),
                          None)

    def tearDown(self):
        super(RabbitNotifierTest, self).tearDown()
