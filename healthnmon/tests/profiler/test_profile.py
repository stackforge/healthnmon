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

import os
from healthnmon import test
from healthnmon.profiler import profile_cpu, profile_mem
from healthnmon.tests.profiler import FakeGuppy


class CPUProfileTestCase(test.TestCase):
    """Test case for CPU time memprofile"""
    def setUp(self):
        super(CPUProfileTestCase, self).setUp()
        self.flags(monkey_patch=True,
                   monkey_patch_modules=["example:log_decorator"])

    def test_logging_by_decorator(self):
        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_cpu.profile_cputime_decorator(
            'example_method',
            example_method)

        self.assertEqual(3, decorator_method(1, 2))

    def test_cpuprofile_monkey_patch_false(self):
        self.flags(monkey_patch=False)

        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_cpu.profile_cputime_decorator(
            'example_method',
            example_method)

        self.assertEqual(3, decorator_method(1, 2))

    def test_cpuprofile_no_monkey_patch_modules(self):
        self.flags(monkey_patch_modules=[])

        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_cpu.profile_cputime_decorator(
            'example_method',
            example_method)

        self.assertEqual(3, decorator_method(1, 2))

    def test_cpuprofile_invalid_monkey_patch_module(self):
        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_cpu.profile_cputime_decorator(
            'dummy_method',
            example_method)

        self.assertEqual(3, decorator_method(1, 2))

    def test_cpuprofile_add_monkey_patch_module(self):
        self.flags(monkey_patch_modules=[])

        profile_cpu.add_module('example_method_new')

        self.assertTrue('example_method_new' in profile_cpu.modules)

    def test_cpuprofile_delete_monkey_patch_module(self):
        self.flags(monkey_patch_modules=[])

        profile_cpu.add_module('example_method_new')
        profile_cpu.delete_module('example_method_new')

        self.assertFalse('example_method_new' in profile_cpu.modules)

    def tearDown(self):
        profile_cpu.modules = []
        super(CPUProfileTestCase, self).tearDown()


class MemorymemprofileTestCase(test.TestCase):
    """Test case for Memory memprofile"""
    profile_mem.hpy = FakeGuppy.hpy
    hpy_class = profile_mem.hpy

    def setUp(self):
        super(MemorymemprofileTestCase, self).setUp()
        self.flags(healthnmon_log_dir='.')
        self.path_to_file = 'healthnmon_memprofile.hpy'
        profile_mem.hpy = FakeGuppy.hpy
        self.h = profile_mem.hpy()
        profile_mem.setref = False

    def test_enable_memprofile_by_decorator(self):

        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_mem.profile_memory_decorator(
            'example_method',
            example_method)

        profile_mem.modules_profiling_status['example_method'] = True

        rt = decorator_method(1, 2)
        self.assertNotEqual(profile_mem.h, None)
        self.assertEqual(3, rt)

    def test_enable_memprofile_setref_True(self):
        profile_mem.setref = True

        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_mem.profile_memory_decorator(
            'example_method',
            example_method)

        profile_mem.modules_profiling_status['example_method'] = True

        rt = decorator_method(1, 2)
        self.assertNotEqual(profile_mem.h, None)
        self.assertEqual(3, rt)

    def test_memprofile_no_dumpfile(self):
        self.flags(healthnmon_log_dir='')

        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_mem.profile_memory_decorator(
            'example_method',
            example_method)
        profile_mem.modules_profiling_status['example_method'] = True

        rt = decorator_method(1, 2)

        self.assertFalse(os.path.isfile(self.path_to_file))
        self.assertEqual(3, rt)

    def test_memprofile_throwException(self):
        def example_method(arg1, arg2):
            return arg1 + arg2
        self.assertRaises(Exception, profile_mem.profile_memory_decorator(
            'example_method', example_method))

    def test_disable_memprofile_by_decorator(self):
        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_mem.profile_memory_decorator(
            'example_method',
            example_method)
        profile_mem.modules_profiling_status['example_method'] = False

        rt = decorator_method(1, 2)

        self.assertEqual(profile_mem.h, None)
        self.assertEqual(3, rt)

    def test_initiliaze_memprofile(self):
        profile_mem.h = profile_mem.hpy()

        def example_method(arg1, arg2):
            return arg1 + arg2

        decorator_method = profile_mem.profile_memory_decorator(
            'example_method',
            example_method)
        profile_mem.modules_profiling_status['example_method'] = True

        rt = decorator_method(1, 2)

        self.assertEqual(3, rt)

    def tearDown(self):
        if(os.path.isfile(self.path_to_file)):
            os.remove(self.path_to_file)
        profile_mem.h = None
        super(MemorymemprofileTestCase, self).tearDown()
