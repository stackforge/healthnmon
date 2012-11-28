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

import unittest
from test_healthnmon import HealthnmonTest
from test_storagevolume import StorageVolumeTest
from test_util import UtilTest
from test_vm import VMTest
from test_vmhosts import VmHostsTest
from test_subnet import SubnetTest
from test_virtualswitch import VirtualSwitchTest
from test_base import BaseControllerTest


def run_tests():
    loader = unittest.TestLoader()
    healthnmon_suite = loader.loadTestsFromTestCase(HealthnmonTest)
    storage_suite = loader.loadTestsFromTestCase(StorageVolumeTest)
    util_suite = loader.loadTestsFromTestCase(UtilTest)
    vm_suite = loader.loadTestsFromTestCase(VMTest)
    subnet_suite = loader.loadTestsFromTestCase(SubnetTest)
    vmhosts_suite = loader.loadTestsFromTestCase(VmHostsTest)
    virtual_switch_suite = \
        loader.loadTestsFromTestCase(VirtualSwitchTest)
    base_suite = loader.loadTestsFromTestCase(BaseControllerTest)
    alltests = [
        healthnmon_suite,
        storage_suite,
        util_suite,
        vm_suite,
        subnet_suite,
        vmhosts_suite,
        virtual_switch_suite,
        base_suite
    ]
    result = unittest.TestResult()
    for test in alltests:
        test.run(result)


if __name__ == '__main__':
    run_tests()
