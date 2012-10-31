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
import healthnmon.notifier.api as notifier_api


class APiTest(test.TestCase):

    ''' TestCase for healthnmon.notifier.api '''

    def setUp(self):
        super(APiTest, self).setUp()
        self.flags(healthnmon_default_notification_level='INFO',
         healthnmon_notification_drivers=[
                 'healthnmon.notifier.rabbit_notifier',
                 'healthnmon.notifier.atlas_event_notifier'
                  ])

    def testNotify(self):
        self.flags(healthnmon_default_notification_level='INFO')
        event_type = 'LifeCycle.Vm.Reconfigured'
        publisher_id = 'healthnmon.unittest'
        priority = 'INFO'
        payload = {'entity_id': '024c1520-f836-47f7-3c91-df627096f8ab'}
        self.assertEquals(notifier_api.notify(publisher_id, event_type,
                          priority, payload), None)

    def testNotifyForPriorityException(self):
        event_type = 'LifeCycle.Vm.Reconfigured'
        publisher_id = 'healthnmon.unittest'
        priority = 'TEST'
        payload = {'entity_id': '024c1520-f836-47f7-3c91-df627096f8ab'}
        self.assertRaises(
            notifier_api.BadPriorityException,
            notifier_api.notify,
            publisher_id,
            event_type,
            priority,
            payload,
            )

    def testNotifierException(self):
        self.flags(healthnmon_notification_drivers=['healthnmon.tests.\
notifier.test_api.ExceptionNotifier']
                   )
        event_type = 'LifeCycle.Vm.Reconfigured'
        publisher_id = 'healthnmon.unittest'
        priority = 'INFO'
        payload = {'entity_id': '024c1520-f836-47f7-3c91-df627096f8ab'}
        notifier_api.notify(publisher_id, event_type, priority, payload)

    def testNotifierClassNotfound(self):
        self.flags(healthnmon_notification_drivers=['healthnmon.tests.\
notifier.test_api.ExceptionNotifier1']
                   )
        event_type = 'LifeCycle.Vm.Reconfigured'
        publisher_id = 'healthnmon.unittest'
        priority = 'INFO'
        payload = {'entity_id': '024c1520-f836-47f7-3c91-df627096f8ab'}
        notifier_api.notify(publisher_id, event_type, priority, payload)

    def tearDown(self):
        super(APiTest, self).tearDown()


class ExceptionNotifier(object):

    '''Test notifier which raises a exception for covering exception block
    '''

    def notify(self, message):
        raise Exception('Test Exception')
