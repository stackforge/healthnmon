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

from healthnmon.profiler import profile_cpu, helper
from healthnmon.tests.profiler import example_a
from healthnmon import log
from healthnmon import test
import healthnmon
import logging
import os


class CPUProfileMonkeyPatchingTestCase(test.TestCase):
    """Unit test for helper.profile_cputime in healthnmon."""
    def setUp(self):
        super(CPUProfileMonkeyPatchingTestCase, self).setUp()
        self.example_package = 'healthnmon.tests.profiler.'

    def test_enable_profile_cputime_by_decorator(self):
        helper.profile_cputime(
            self.example_package + 'example_a',
            self.example_package + 'example_cpu_profile_decorator', True)

        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION = []

        self.assertEqual('Example function', example_a.example_function_a())
        exampleA = example_a.ExampleClassA()
        exampleA.example_method()
        ret_a = exampleA.example_method_add(3, 5)
        self.assertEqual(ret_a, 8)

        package_a = self.example_package + 'example_a.'
        self.assertTrue(package_a + 'example_function_a' in
                        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)

        self.assertTrue(package_a + 'ExampleClassA.example_method' in
                        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)
        self.assertTrue(package_a + 'ExampleClassA.example_method_add' in
                        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)
        self.assertEqual(len(profile_cpu.modules), 1)

    def test_disable_profile_cputime_by_decorator(self):
        helper.profile_cputime(
            self.example_package + 'example_a',
            self.example_package + 'example_cpu_profile_decorator', False)

        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION = []

        self.assertEqual('Example function', example_a.example_function_a())
        exampleA = example_a.ExampleClassA()
        exampleA.example_method()
        ret_a = exampleA.example_method_add(3, 5)
        self.assertEqual(ret_a, 8)

        package_a = self.example_package + 'example_a.'
        self.assertTrue(package_a + 'example_function_a' in
                        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)

        self.assertTrue(package_a + 'ExampleClassA.example_method' in
                        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)
        self.assertTrue(package_a + 'ExampleClassA.example_method_add' in
                        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)
        self.assertEqual(len(profile_cpu.modules), 0)

    def test_profile_cputime_twice_by_samedecorator(self):
        helper.profile_cputime(
            self.example_package + 'example_a',
            self.example_package + 'example_cpu_profile_decorator', True)
        self.assertEqual(len(profile_cpu.modules), 1)

        helper.profile_cputime(
            self.example_package + 'example_a',
            self.example_package + 'example_cpu_profile_decorator', False)
        self.assertEqual(len(profile_cpu.modules), 0)

    def test_profile_cputime_throw_excsption(self):
        helper.profile_cputime(
            self.example_package + 'example_a_not_available',
            self.example_package + 'example_cpu_profile_decorator', True)
        healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION = []

        package_a = self.example_package + 'example_a.'
        self.assertFalse(package_a + 'example_function_a' in
                         healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)
        self.assertFalse(package_a + 'ExampleClassA.example_method' in
                         healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)
        self.assertFalse(package_a + 'ExampleClassA.example_method_add' in
                         healthnmon.tests.profiler.CPU_PROFILE_CALLED_FUNCTION)

    def tearDown(self):
        profile_cpu.modules = []
        super(CPUProfileMonkeyPatchingTestCase, self).tearDown()


class MemoryProfileMonkeyPatchingTestCase(test.TestCase):
    """Unit test for helper.profile_memory in healthnmon."""
    def setUp(self):
        super(MemoryProfileMonkeyPatchingTestCase, self).setUp()
        self.example_package = 'healthnmon.tests.profiler.'

    def example_method(arg1, arg2):
        return arg1 + arg2

    def test_enable_profile_memory_by_decorator(self):

        helper.profile_memory(
            self.example_package + 'example_a.example_function_a',
            self.example_package + 'example_memory_profile_decorator',
            True, True)

        healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION = []

        self.assertEqual('Example function', example_a.example_function_a())
        exampleA = example_a.ExampleClassA()
        exampleA.example_method()
        ret_a = exampleA.example_method_add(3, 5)
        self.assertEqual(ret_a, 8)

        package_a = self.example_package + 'example_a.'
        self.assertTrue(
            package_a + 'example_function_a' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)
        self.assertFalse(
            package_a + 'ExampleClassA.example_method' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)
        self.assertFalse(
            package_a + 'ExampleClassA.example_method_add' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)

    def test_profile_memory_twice_by_samedecorator(self):

        helper.profile_memory(
            self.example_package + 'example_a.example_function_a',
            self.example_package + 'example_memory_profile_decorator',
            True, True)

        helper.profile_memory(
            self.example_package + 'example_a.example_function_a',
            self.example_package + 'example_memory_profile_decorator',
            False, True)

        healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION = []

        self.assertEqual('Example function', example_a.example_function_a())
        exampleA = example_a.ExampleClassA()
        exampleA.example_method()
        ret_a = exampleA.example_method_add(3, 5)
        self.assertEqual(ret_a, 8)

        package_a = self.example_package + 'example_a.'
        self.assertTrue(
            package_a + 'example_function_a' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)

        self.assertFalse(
            package_a + 'ExampleClassA.example_method' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)
        self.assertFalse(
            package_a + 'ExampleClassA.example_method_add' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)

    def test_profile_memory_throw_exception(self):
        helper.profile_memory(
            self.example_package + 'example_a.example_a_not_available',
            self.example_package + 'example_memory_profile_decorator',
            True, True)
        healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION = []

        package_a = self.example_package + 'example_a.'
        self.assertFalse(
            package_a + 'example_function_a' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)

        self.assertFalse(
            package_a + 'ExampleClassA.example_method' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)
        self.assertFalse(
            package_a + 'ExampleClassA.example_method_add' in
            healthnmon.tests.profiler.MEMORY_PROFILE_CALLED_FUNCTION)


class HelperTestCase(test.TestCase):
    current_dir = os.path.join(os.path.dirname(__file__))
    log_config_file_path = os.path.join(current_dir,
                                        '../healthnmon_testlog.conf')

    def setUp(self):
        super(HelperTestCase, self).setUp()
        self.flags(logging_greenthread_format_string="GTHREAD ID | "
                                                     "%(levelname)s | "
                                                     "%(gthread_id)d | "
                                                     "%(message)s",
                   healthnmon_collector_log_config=self.log_config_file_path)

        logdir = 'healthnmon'
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        log.healthnmon_collector_setup()

    def test_set_log_level_DEBUG(self):
        self.log = log.getLogger('healthnmon.example')
        self.assertEqual(logging.INFO, self.log.logger.getEffectiveLevel())

        helper.setLogLevel('DEBUG', 'healthnmon.example')
        self.assertEqual(logging.DEBUG, self.log.logger.getEffectiveLevel())

    def test_set_log_level_AUDIT(self):
        self.log = log.getLogger('healthnmon.example')
        self.assertEqual(logging.INFO, self.log.logger.getEffectiveLevel())

        helper.setLogLevel('AUDIT', 'healthnmon.example')
        self.assertEqual(
            log.logging.AUDIT, self.log.logger.getEffectiveLevel())

    def test_set_log_level_ERROR(self):
        self.log = log.getLogger('healthnmon.example')
        self.assertEqual(logging.INFO, self.log.logger.getEffectiveLevel())

        helper.setLogLevel('ERROR', 'healthnmon.example')
        self.assertEqual(logging.ERROR, self.log.logger.getEffectiveLevel())

    def test_set_log_level_healthnmon(self):
        self.log = log.getLogger('healthnmon.example')
        self.assertEqual(logging.INFO, self.log.logger.getEffectiveLevel())

        helper.setLogLevel('DEBUG', 'healthnmon')
        self.assertEqual(logging.DEBUG, self.log.logger.getEffectiveLevel())
        self.assertEqual(
            logging.DEBUG, logging.getLogger().getEffectiveLevel())

    def test_set_log_level_healthnmon_debug(self):
        self.log = log.getLogger('healthnmon.example')
        self.assertEqual(logging.INFO, self.log.logger.getEffectiveLevel())

        helper.setLogLevel('debug', 'healthnmon')
        self.assertEqual(logging.DEBUG, self.log.logger.getEffectiveLevel())
        self.assertEqual(
            logging.DEBUG, logging.getLogger().getEffectiveLevel())

    def test_set_log_level_healthnmon_invalid_loglevel(self):
        self.log = log.getLogger('healthnmon.example')
        self.assertEqual(logging.INFO, self.log.logger.getEffectiveLevel())

        self.assertRaises(Exception, helper.setLogLevel, 'test', 'healthnmon')
        self.assertNotEqual(logging.DEBUG, self.log.logger.getEffectiveLevel())
        self.assertNotEqual(
            logging.DEBUG, logging.getLogger().getEffectiveLevel())
