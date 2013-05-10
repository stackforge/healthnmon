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
Base Unit Test Class for Healthnmon
"""


from nova.openstack.common import timeutils as utils
import unittest
import mox
import shutil
import stubout
import os
from oslo.config import cfg
import healthnmon

FLAGS = cfg.CONF
healthnmon_path = os.path.abspath(
    os.path.join(healthnmon.get_healthnmon_location(), '../'))


class TestCase(unittest.TestCase):
    """Test case base class for all unit tests."""

    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()
        self.start = utils.utcnow()
        shutil.copyfile(os.path.join(healthnmon_path, FLAGS.sqlite_clean_db),
                        os.path.join(healthnmon_path, FLAGS.sqlite_db))

        # emulate some of the mox stuff, we can't use the metaclass
        # because it screws with our generators
        self.mox = mox.Mox()
        self.stubs = stubout.StubOutForTesting()
        self.injected = []
        self._services = []
        self._overridden_opts = []

    def tearDown(self):
        """Runs after each test method to tear down test environment."""
        try:
            self.mox.UnsetStubs()
            self.stubs.UnsetAll()
            self.stubs.SmartUnsetAll()
            self.mox.VerifyAll()
            super(TestCase, self).tearDown()
        finally:
            # Clean out fake_rabbit's queue if we used it

            # Reset any overridden flags
            self.reset_flags()

            # Stop any timers
            for x in self.injected:
                try:
                    x.stop()
                except AssertionError:
                    pass

            # Kill any services
            for x in self._services:
                try:
                    x.kill()
                except Exception:
                    pass

            # Delete attributes that don't start with _ so they don't pin
            # memory around unnecessarily for the duration of the test
            # suite
            for key in [k for k in self.__dict__.keys() if k[0] != '_']:
                del self.__dict__[key]

    def flags(self, **kw):
        """Override flag variables for a test."""
        for k, v in kw.iteritems():
            FLAGS.set_override(k, v)
            self._overridden_opts.append(k)

    def reset_flags(self):
        """Resets all flag variables for the test.

        Runs after each test.

        """
        for k in self._overridden_opts:
            FLAGS.set_override(k, None)
        self._overridden_opts = []

    def assertIn(self, a, b, *args, **kwargs):
        """Python < v2.7 compatibility.  Assert 'a' in 'b'"""
        try:
            f = super(TestCase, self).assertIn
        except AttributeError:
            self.assertTrue(a in b, *args, **kwargs)
        else:
            f(a, b, *args, **kwargs)

    def assertNotIn(self, a, b, *args, **kwargs):
        """Python < v2.7 compatibility.  Assert 'a' NOT in 'b'"""
        try:
            f = super(TestCase, self).assertNotIn
        except AttributeError:
            self.assertFalse(a in b, *args, **kwargs)
        else:
            f(a, b, *args, **kwargs)
