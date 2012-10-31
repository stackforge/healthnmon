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

from nova import flags
import unittest
import os
import logging
import shutil
import healthnmon

healthnmon_path = os.path.abspath(os.path.join(healthnmon.get_healthnmon_location(), '../'))

FLAGS = flags.FLAGS
FLAGS.set_default('sqlite_db', 'tests.sqlite')
FLAGS.set_default('sqlite_synchronous', False)
sql_connection_url = "sqlite:///" + str(healthnmon_path) + "/$sqlite_db"
FLAGS.set_default("sql_connection", sql_connection_url)


class TestCase(unittest.TestCase):

    """Base class for all DB unit tests."""

    def setUp(self):
        """Run before each test method to initialize DB"""
        logging.basicConfig()
        super(TestCase, self).setUp()
        shutil.copyfile(os.path.join(healthnmon_path, FLAGS.sqlite_clean_db),
                        os.path.join(healthnmon_path, FLAGS.sqlite_db))
