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
import healthnmon
import os


class HealthnMonTestCase(test.TestCase):

    ''' TestCase for healthnmon.__init__ '''

    def test_get_healthnmon_location(self):
        healthnmon_package_loc = healthnmon.get_healthnmon_location()
        self.assertNotEqual(healthnmon_package_loc, None)
        init_file_path = os.path.join(healthnmon_package_loc,
                '__init__.py')
        init_exists = os.path.exists(init_file_path)
        self.assertTrue(init_exists,
                        _('__init__.py file not existing in %s'
                        % healthnmon_package_loc))
