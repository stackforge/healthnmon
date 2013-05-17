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

""" Healthnmon logging handler.
This module adds to logging functionality by adding the option to specify
current green thread id/thread id when calling the various log methods.
"""

import logging
import logging.handlers
import cStringIO
import traceback
from oslo.config import cfg
from eventlet import greenthread
import zipfile
import os


log_opts = [
    cfg.StrOpt('healthnmon_log_dir',
               default='/var/log/healthnmon',
               help='Log directory for healthnmon'),
    cfg.StrOpt('healthnmon_collector_log_config',
               default='/etc/healthnmon/logging-healthnmon-collector.conf',
               help='Log configuration file for healthnmon collector'),
    cfg.StrOpt('healthnmon_virtproxy_log_config',
               default='/etc/healthnmon/logging-healthnmon-virtproxy.conf',
               help='Log configuration file for healthnmon virtproxy'),
    cfg.StrOpt('healthnmon_manage_log_config',
               default='/etc/healthnmon/logging-healthnmon-manage.conf',
               help='Log configuration file for healthnmon'),
    cfg.StrOpt('healthnmon_logging_audit_format_string',
               default='%(asctime)s,%(componentId)s,%(orgId)s,%(orgId)s,\
               %(domain)s,%(userId)s,%(loggingId)s,%(taskId)s,%(sourceIp)s,\
               %(result)s,%(action)s,%(severity)s,%(name)s,\
               %(objectDescription)s,%(message)s',
               help='format string to use for logging audit log messages'),
    cfg.StrOpt('logging_greenthread_format_string',
               default='%(asctime)s | %(levelname)s | \
               %(name)s | %(gthread_id)d | '
                       '%(message)s',
               help='format string to use for log messages \
               with green thread id'),
    cfg.StrOpt('logging_thread_format_string',
               default='%(asctime)s | %(levelname)s | %(name)s | %(thread)d | '
                       '%(message)s',
               help='format string to use for log messages \
               with green thread id'),
    cfg.StrOpt('logging_greenthread_exception_prefix',
               default='%(asctime)s | TRACE | %(name)s | %(gthread_id)d | ',
               help='prefix each line of exception output with this format'),
    cfg.StrOpt('logging_thread_exception_prefix',
               default='%(asctime)s | TRACE | %(name)s | %(thread)d | ',
               help='prefix each line of exception output with this format'),
]

CONF = cfg.CONF
CONF.register_opts(log_opts)


# AUDIT level
logging.AUDIT = logging.INFO + 1
logging.addLevelName(logging.AUDIT, 'AUDIT')


class HealthnmonLogAdapter(logging.LoggerAdapter):
    """ Healthnmon logging handler that extends default logger to include
        green thread/thread identifier """
    warn = logging.LoggerAdapter.warning

    def __init__(self, logger):
        self.logger = logger

    def audit(self, msg, *args, **kwargs):
        self.log(logging.AUDIT, msg, *args, **kwargs)

    def process(self, msg, kwargs):
        """Uses hash of current green thread object for unqiue identifier """
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        extra = kwargs['extra']

        if greenthread.getcurrent() is not None:
            extra.update({'gthread_id': hash(greenthread.getcurrent())})

        extra['extra'] = extra.copy()
        return msg, kwargs


class HealthnmonFormatter(logging.Formatter):
    """Thread aware formatter configured through flags.

    The flags used to set format strings are: logging_greenthread_format_string
    and logging_thread_format_string.

    For information about what variables are available for the formatter see:
    http://docs.python.org/library/logging.html#formatter
    """

    def format(self, record):
        """Uses green thread id if available, otherwise thread id is used ."""
        if 'gthread_id' not in record.__dict__:
            self._fmt = CONF.logging_thread_format_string
        else:
            self._fmt = CONF.logging_greenthread_format_string

        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info, record)
        return logging.Formatter.format(self, record)

    def formatException(self, exc_info, record=None):
        """Format exception output with
        CONF.healthnmon_logging_exception_prefix."""
        if not record:
            return logging.Formatter.formatException(self, exc_info)
        stringbuffer = cStringIO.StringIO()
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2],
                                  None, stringbuffer)
        lines = stringbuffer.getvalue().split('\n')
        stringbuffer.close()
        if 'gthread_id' not in record.__dict__:
            exception_prefix = CONF.logging_thread_exception_prefix
        else:
            exception_prefix = CONF.logging_greenthread_exception_prefix
        if exception_prefix.find('%(asctime)') != -1:
            record.asctime = self.formatTime(record, self.datefmt)
        formatted_lines = []
        for line in lines:
            pl = exception_prefix % record.__dict__
            fl = '%s%s' % (pl, line)
            formatted_lines.append(fl)
        return '\n'.join(formatted_lines)


class HealthnmonLogHandler(logging.handlers.RotatingFileHandler):
    """Size based rotating file handler which zips the backup files
    """
    def __init__(self, filename, mode='a', maxBytes=104857600, backupCount=20,
                 encoding='utf-8'):
        logging.handlers.RotatingFileHandler.__init__(
            self, filename, mode, maxBytes, backupCount, encoding)

    def doRollover(self):
        logging.handlers.RotatingFileHandler.doRollover(self)
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d.gz" % (self.baseFilename, i)
                dfn = "%s.%d.gz" % (self.baseFilename, i + 1)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.baseFilename + ".1"
            compressed_log_file = zipfile.ZipFile(dfn + ".gz", "w")
            compressed_log_file.write(dfn, os.path.basename(
                dfn), zipfile.ZIP_DEFLATED)
            compressed_log_file.close()
            os.remove(dfn)


class HealthnmonAuditFilter(logging.Filter):

    def filter(self, record):
        if record.levelno == logging.AUDIT:
            return True


class HealthnmonAuditFormatter(HealthnmonFormatter):
    """Format audit messages as per the audit logging format"""
    def format(self, record):
        self._fmt = CONF.healthnmon_logging_audit_format_string

        if 'componentId' not in record.__dict__:
            record.__dict__['componentId'] = 'Healthnmon'
        if 'orgId' not in record.__dict__:
            record.__dict__['orgId'] = ''
        if 'domain' not in record.__dict__:
            record.__dict__['domain'] = ''
        if 'userId' not in record.__dict__:
            record.__dict__['userId'] = ''
        if 'loggingId' not in record.__dict__:
            record.__dict__['loggingId'] = ''
        if 'taskId' not in record.__dict__:
            record.__dict__['taskId'] = ''
        if 'sourceIp' not in record.__dict__:
            record.__dict__['sourceIp'] = ''
        if 'result' not in record.__dict__:
            record.__dict__['result'] = ''
        if 'action' not in record.__dict__:
            record.__dict__['action'] = ''
        if 'severity' not in record.__dict__:
            record.__dict__['severity'] = ''
        if 'objectDescription' not in record.__dict__:
            record.__dict__['objectDescription'] = ''

        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info, record)
        return logging.Formatter.format(self, record)


class HealthnmonAuditHandler(HealthnmonLogHandler):
    """"""
    def __init__(self, filename, mode='a', maxBytes=104857600, backupCount=20,
                 encoding='utf-8'):
        HealthnmonLogHandler.__init__(
            self, filename, mode, maxBytes, backupCount, encoding)
        self.addFilter(HealthnmonAuditFilter())

# def handle_exception(type, value, tb):
#    extra = {}
#    if CONF.verbose:
#        extra['exc_info'] = (type, value, tb)
#    getLogger().critical(str(value), **extra)


def healthnmon_collector_setup():
    """Setup healthnmon logging."""
    # sys.excepthook = handle_exception

    if CONF.healthnmon_collector_log_config:
        try:
            logging.config.fileConfig(CONF.healthnmon_collector_log_config)
        except Exception:
            traceback.print_exc()
            raise


def healthnmon_manage_setup():
    """Setup healthnmon logging."""
    # sys.excepthook = handle_exception

    if CONF.healthnmon_manage_log_config:
        try:
            logging.config.fileConfig(CONF.healthnmon_manage_log_config)
        except Exception:
            traceback.print_exc()
            raise


def healthnmon_virtproxy_setup():
    """Setup healthnmon logging."""
    # sys.excepthook = handle_exception

    if CONF.healthnmon_virtproxy_log_config:
        try:
            logging.config.fileConfig(CONF.healthnmon_virtproxy_log_config)
        except Exception:
            traceback.print_exc()
            raise

_loggers = {}


def getLogger(name='healthnmon'):
    if name not in _loggers:
        _loggers[name] = HealthnmonLogAdapter(logging.getLogger(name))
    return _loggers[name]
