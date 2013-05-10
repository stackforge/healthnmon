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
Defines decorator for profiling heathnmon Service
Uses heapy- for memory profiling
"""

from healthnmon import log as logging
from oslo.config import cfg
import traceback
import functools
import os

LOG = logging.getLogger('healthnmon.profiler')
CONF = cfg.CONF

h = None
mem_profile_path = None
hpy = None
modules_profiling_status = {}
setref = None


def profile_memory_decorator(method, fn):
    """ decorator for logging which is used from utils.monkey_patch()

        :param name: name of the function
        :param function: - object of the function
        :returns: function -- decorated function
    """
    @functools.wraps(fn)
    def profile_memory(*args, **kwarg):
        status = modules_profiling_status[method]
        if status:
            import_guupy()
            LOG.info(_('Start memory profiling'))
            init_mem_profiler()
            rt = fn(*args, **kwarg)
            mem_profile()
            LOG.info(_('End memory profiling'))
            return rt
        else:
            return fn(*args, **kwarg)

    return profile_memory


def import_guupy():
    global hpy
    if hpy is None:
        guppy = __import__('guppy', globals(), locals(),
                           ['hpy'], -1)
        hpy = guppy.hpy


def init_mem_profiler():
    """ Intializes the heapy module used for memory profiling """
    global h
    if h is None:
        h = hpy()
        _init_mem_profile_path()


def _init_mem_profile_path():
    global mem_profile_path
    mem_profile_path = _get_memprofile_dumpfile('healthnmon')
    if mem_profile_path:
        open(mem_profile_path, 'a')
        mode = int(CONF.logfile_mode, 8)
        os.chmod(mem_profile_path, mode)


def mem_profile():
    """
    Sets configuration in heapy to
    1) generate and dump memory snapshot
    2) set the reference point for next dump
    """
    try:
        # LOG.debug(_(h.heap()))
        h.heap().dump(mem_profile_path)
        LOG.debug(_("Dumped the memory profiling data "))
        if setref:
            LOG.debug(_("Setting the reference for next \
                memory profiling data "))
            h.setref()
    except:
        LOG.debug(_('Exception occurred %s ') % traceback.format_exc())


def _get_memprofile_dumpfile(binary=None):
    logdir = CONF.healthnmon_log_dir
    if logdir:
        return '%s_memprofile.hpy' % (os.path.join(logdir, binary),)
