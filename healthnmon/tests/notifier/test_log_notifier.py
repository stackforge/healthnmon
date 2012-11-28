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
from healthnmon.notifier import api
import healthnmon.notifier.log_notifier
from nova.openstack.common import context


class LogNotifierTest(test.TestCase):

    ''' TestCase for healthnmon.notifier.log_notifier '''

    def setUp(self):
        super(LogNotifierTest, self).setUp()
        self.context = context.get_admin_context()
        self.flags(healthnmon_default_notification_level='INFO')

    def testNotify(self):
        message = {
            'priority': 'INFO',
            'event_type': 'LifeCycle.Vm.Reconfigured',
            'payload': {'entity_id': '024c1520-f836-47f7-3c91-df627096f8ab'},
            'message_id': '409e109d-41c0-4b75-9019-04aa3329c67b',
        }
        self.assertEquals(
            healthnmon.notifier.log_notifier.notify(self.context, message),
            None)

    def tearDown(self):

#        list_notifier._reset_drivers()

        super(LogNotifierTest, self).tearDown()
