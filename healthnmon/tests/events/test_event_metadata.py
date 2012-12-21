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

"""Unit test for event_metadata module
"""

from nova import test
from healthnmon.events import event_metadata
from healthnmon import notifier
from healthnmon.resourcemodel.healthnmonResourceModel import Vm


class EventMetadataTest(test.TestCase):

    """Unit test for event_metadata module
    """

    def setUp(self):
        super(EventMetadataTest, self).setUp()
        self.event_type = 'TestType.TestEvent'
        self.event_category = 'TestCategory'
        self.short_desc_tmpl = 'Short Description %(name)s'
        self.long_desc_tmpl = \
            'Long Description %(name)s : keyword_arg %(test_arg)s'
        self.priority = notifier.api.INFO
        self.metadata = event_metadata.EventMetaData(
            self.event_type,
            self.event_category, self.short_desc_tmpl,
            self.long_desc_tmpl, self.priority)

    def testGet_EventMetaData(self):
        event_type = event_metadata.EVENT_TYPE_VM_CREATED
        meta = event_metadata.get_EventMetaData(event_type)
        self.assertEquals(meta,
                          event_metadata.eventMetadataDict[event_type])

    def testGet_EventMetaData_Exception(self):
        event_type = 'INVALID_NAME'
        self.assertRaises(event_metadata.BadEventTypeException,
                          event_metadata.get_EventMetaData, event_type)

    def testGet_short_desc(self):
        testVm = Vm()
        testVm.name = 'TestVm'
        short_desc = self.metadata.get_short_desc(testVm)
        self.assertEquals(short_desc, self.short_desc_tmpl
                          % {'name': testVm.name})

    def testGet_long_desc(self):
        testVm = Vm()
        testVm.name = 'TestVm'
        test_arg = 'TestArg'
        long_desc = self.metadata.get_long_desc(testVm,
                                                test_arg=test_arg)
        self.assertEquals(long_desc, self.long_desc_tmpl
                          % {'name': testVm.name, 'test_arg': test_arg})

    def testGet_topic_name(self):
        objuuid = 'ABCD123'
        topic_name = self.metadata.get_topic_name(objuuid)
        exp_topic_name = '.'.join(['healthnmon_notification',
                                  self.priority, self.event_category,
                                  self.event_type, objuuid])
        self.assertEquals(topic_name, exp_topic_name)

    def testGet_event_fully_qal_name(self):
        exp_qual_name = '.'.join([self.event_category, self.event_type])
        qual_name = self.metadata.get_event_fully_qal_name()
        self.assertEquals(qual_name, exp_qual_name)

    def tearDown(self):
        super(EventMetadataTest, self).tearDown()
