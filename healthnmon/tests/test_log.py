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

import cStringIO
import logging
import mox
import os
import time
import sys
from nova import test
from healthnmon import log
from healthnmon.log import HealthnmonFormatter
from healthnmon.log import HealthnmonAuditFilter
from healthnmon.log import HealthnmonAuditFormatter
from healthnmon.log import HealthnmonAuditHandler
from eventlet import greenthread


class HealthnmonLoggerTestCase(test.TestCase):
    """Test cases for Healthnmon log adapter"""

    log_config_file_path = os.path.join(
        os.path.join(os.path.dirname(__file__)),
        'healthnmon_testlog.conf')
    manage_log_config_file_path = os.path.join(
        os.path.join(os.path.dirname(__file__)),
        'healthnmon-manage_testlog.conf')

    def setUp(self):
        super(HealthnmonLoggerTestCase, self).setUp()

        self.flags(logging_greenthread_format_string="GTHREAD ID | "
                                                     "%(levelname)s | "
                                                     "%(gthread_id)d | "
                                                     "%(message)s",
                   logging_thread_format_string="THREAD ID | "
                                                "%(thread)d | "
                                                "%(message)s",
                   healthnmon_log_config=self.log_config_file_path,
                   healthnmon_manage_log_config=self.manage_log_config_file_path)

        logdir = 'healthnmon'
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        log.setup()
        self.log = log.getLogger()

    def test_loglevel_DEBUG_from_logConf(self):
        self.log.logger.setLevel(logging.DEBUG)
        self.log.debug(_("baz"))
        self.assert_(True)  # didn't raise exception
        self.assertEqual(
            self.log.logger.level, self.log.logger.getEffectiveLevel())

    def test_loglevel_INFO_from_logConf(self):
        self.log.info("baz")
        self.assert_(True)  # didn't raise exception
        self.assertEqual(
            self.log.logger.level, self.log.logger.getEffectiveLevel())

    def test_loglevel_audit_from_logConf(self):
        self.log.logger.setLevel(logging.AUDIT)
        self.log.audit("baz")
        self.assert_(True)  # didn't raise exception
        self.assertEqual(
            self.log.logger.level, self.log.logger.getEffectiveLevel())

    def test_log_handlers(self):
        self.log.info("baz")
        self.assert_(True)  # didn't raise exception
        self.handlers = self.log.logger.handlers
        self.assertEqual(self.handlers[0].__class__.__name__, 'StreamHandler')
        self.assertEqual(
            self.handlers[1].__class__.__name__, 'WatchedFileHandler')
        self.assertEqual(
            self.handlers[2].__class__.__name__, 'HealthnmonAuditHandler')

    def test_loglevel_no_logConf(self):
        self.flags(healthnmon_log_config="dummyfile")

        try:
            log.setup()
        except Exception:
            self.assert_(True)  # raise exception

    def test_loglevel_logConf_None(self):
        self.flags(healthnmon_log_config="")
        log.setup()

        self.assert_(True)  # do not raise exception

    def test_loglevel_manage_logConf_None(self):
        self.flags(healthnmon_manage_log_config="")
        log.healthnmon_manage_setup()

        self.assert_(True)  # do not raise exception

    def test_log_no_green_thread(self):
        self.mox.StubOutWithMock(greenthread, 'getcurrent')
        greenthread.getcurrent().AndReturn(None)
        self.mox.ReplayAll()

        self.log.info("baz")
        self.assert_(True)  # do not raise exception

    def test_log_with_kwarsg(self):
        self.log.info("baz", extra={})
        self.assert_(True)  # didn't raise exception
        self.assertEqual(
            self.log.logger.level, self.log.logger.getEffectiveLevel())

    def test_loglevel_INFO_from_manage_logConf(self):
        log.healthnmon_manage_setup()
        self.log.info("baz")
        self.assert_(True)  # didn't raise exception
        self.assertEqual(
            self.log.logger.level, self.log.logger.getEffectiveLevel())

    def test_loglevel_no_manage_logConf(self):
        self.flags(healthnmon_manage_log_config="dummyfile")

        try:
            log.healthnmon_manage_setup()
        except Exception:
            self.assert_(True)  # raise exception


class HealthnmonFormatterTestCase(test.TestCase):
    """Test cases for Healthnmon formatter"""
    def setUp(self):
        super(HealthnmonFormatterTestCase, self).setUp()

        self.flags(logging_greenthread_format_string="GTHREAD ID | "
                                                     "%(gthread_id)d | "
                                                     "%(message)s",
                   logging_thread_format_string="THREAD ID | "
                                                "%(message)s")
        self.log = log.getLogger()
        self.stream = cStringIO.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.log.logger.addHandler(self.handler)
        self.formatter = log.HealthnmonFormatter()
        self.handler.setFormatter(self.formatter)
        self.log.logger.addHandler(self.handler)
        self.level = self.log.logger.getEffectiveLevel()
        self.log.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        self.log.logger.setLevel(self.level)
        self.log.logger.removeHandler(self.handler)
        super(HealthnmonFormatterTestCase, self).tearDown()

    def test_log_gthreadId(self):
        self.log.debug("foo")
        gthread_id = hash(greenthread.getcurrent())
        expected = "GTHREAD ID | %d | foo\n" % gthread_id
        self.assertEqual(expected, self.stream.getvalue())

    def test_log_healthnmon_formatter_format(self):
        formatter = HealthnmonFormatter()

        try:
            raise Exception('This is exceptional')
        except Exception as ex:
            exc_info = sys.exc_info()
            logrecord = logging.LogRecord('healthnmon', 10, '/root/git/healthnmon/healthnmon/log.py', 117, 'foo', None, exc_info)
            logrecord.asctime = time.time()
            logrecord.instance = exc_info
            result = formatter.format(logrecord)
            self.assert_(True)

    def test_log_healthnmon_formatter_formatexception(self):
        formatter = HealthnmonFormatter()

        try:
            raise Exception('This is exceptional')
        except Exception as ex:
            exc_info = sys.exc_info()
            logrecord = logging.LogRecord('healthnmon', 10, '/root/git/healthnmon/healthnmon/log.py', 117, 'foo', None, exc_info)
            result = formatter.formatException(exc_info, logrecord)
            self.assert_(True)

    def test_log_healthnmon_formatter_formatexception_greenthread(self):
        formatter = HealthnmonFormatter()

        try:
            raise Exception('This is exceptional')
        except Exception as ex:
            exc_info = sys.exc_info()
            logrecord = logging.LogRecord('healthnmon', 10, '/root/git/healthnmon/healthnmon/log.py', 117, 'foo', None, exc_info)
            logrecord.gthread_id = 10500
            result = formatter.formatException(exc_info, logrecord)
            self.assert_(True)

    def test_log_healthnmon_formatter_without_logrecord(self):
        formatter = HealthnmonFormatter()

        try:
            raise Exception('This is exceptional')
        except Exception as ex:
            exc_info = sys.exc_info()
            formatter.formatException(exc_info)
            self.assert_(True)

    def test_log_threadId(self):
        self.mox.StubOutWithMock(self.log.logger, 'makeRecord')
        logrecord = logging.LogRecord(
            'healthnmon', 10, None, 117, 'foo', None, None, None)
        self.log.logger.makeRecord(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(logrecord)
        self.mox.ReplayAll()

        self.log.debug("foo")
        self.assert_(True)
        expected = 'THREAD ID | foo\n'
        self.assertEqual(expected, self.stream.getvalue())


class HealthnmonAuditFormatterTestCase(test.TestCase):

    def setUp(self):
        super(HealthnmonAuditFormatterTestCase, self).setUp()
        self.log = log.getLogger()
        self.stream = cStringIO.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.log.logger.addHandler(self.handler)
        self.formatter = log.HealthnmonFormatter()
        self.handler.setFormatter(self.formatter)
        self.log.logger.addHandler(self.handler)
        self.level = self.log.logger.getEffectiveLevel()
        self.log.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        self.log.logger.setLevel(self.level)
        self.log.logger.removeHandler(self.handler)
        super(HealthnmonAuditFormatterTestCase, self).tearDown()

    def test_log_healthnmon_audit_formatter_format_without_optional_values(self):
        formatter = HealthnmonAuditFormatter()

        logrecord = logging.LogRecord('healthnmon', 10, '/root/git/healthnmon/healthnmon/log.py', 117, 'foo', None, None)
        logrecord.asctime = time.time()
        result = formatter.format(logrecord)
        self.assert_(True)

    def test_log_healthnmon_audit_formatter_format_with_optional_values(self):
        formatter = HealthnmonAuditFormatter()

        logrecord = logging.LogRecord('healthnmon', 10, '/root/git/healthnmon/healthnmon/log.py', 117, 'foo', None, None)
        logrecord.componentId = "Healthnmon"
        logrecord.orgId = "TestOrgId"
        logrecord.domain = "TestDomain"
        logrecord.userId = "TestUserId"
        logrecord.loggingId = "L123"
        logrecord.taskId = "T123"
        logrecord.sourceIp = "localhost"
        logrecord.result = "SUCCESS"
        logrecord.action = "NOOP"
        logrecord.severity = "INFO"
        logrecord.object = "TestObject"
        logrecord.objectDescription = "TestDescription"
        logrecord.asctime = time.time()
        result = formatter.format(logrecord)
        self.assert_(True)

    def test_log_healthnmon_audit_formatter(self):
        formatter = HealthnmonAuditFormatter()

        try:
            raise Exception('This is exceptional')
        except Exception as ex:
            exc_info = sys.exc_info()
            logrecord = logging.LogRecord('healthnmon', 10, '/root/git/healthnmon/healthnmon/log.py', 117, 'foo', None, exc_info)
            logrecord.asctime = time.time()
            logrecord.instance = exc_info
            result = formatter.format(logrecord)
            self.assert_(True)


class HealthnmonAuditHandlerTestCase(test.TestCase):

    def setUp(self):
        super(HealthnmonAuditHandlerTestCase, self).setUp()

    def test_log_healthnmon_audit_handler(self):
        handler = HealthnmonAuditHandler("Test.log")
        self.assertEqual(
            handler.filters[0].__class__.__name__, 'HealthnmonAuditFilter')

    def tearDown(self):
        super(HealthnmonAuditHandlerTestCase, self).tearDown()


class HealthnmonAuditFilterTestCase(test.TestCase):

    def setUp(self):
        super(HealthnmonAuditFilterTestCase, self).setUp()
        logging.AUDIT = logging.INFO + 1
        logging.addLevelName(logging.AUDIT, 'AUDIT')

    def test_log_healthnmon_audit_filter_for_audit_log(self):
        filter = HealthnmonAuditFilter()

        logrecord = logging.LogRecord('healthnmon', 10, '/root/git/healthnmon/healthnmon/log.py', 117, 'foo', None, None)
        logrecord.objectDescription = "TestDescription"
        logrecord.asctime = time.time()
        logrecord.levelno = logging.AUDIT

        self.assertTrue(filter.filter(logrecord))

    def test_log_healthnmon_audit_filter_for_nonaudit_log(self):
        filter = HealthnmonAuditFilter()

        logrecord = logging.LogRecord('healthnmon', 10, '/root/git/healthnmon/healthnmon/log.py', 117, 'foo', None, None)
        logrecord.objectDescription = "TestDescription"
        logrecord.asctime = time.time()
        logrecord.levelno = logging.INFO

        self.assertFalse(filter.filter(logrecord))

    def tearDown(self):
        super(HealthnmonAuditFilterTestCase, self).tearDown()
