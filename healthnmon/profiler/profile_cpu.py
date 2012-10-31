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
Defines decorator that provides details on time spent in each function in specified
modules which is used from utils.monkey_patch()
"""

from healthnmon import log as logging
from nova import flags
import functools
import time

FLAGS = flags.FLAGS
LOG = logging.getLogger(__name__)

modules = []


def profile_cputime_decorator(name, fn):
    """ decorator for logging which is used from utils.monkey_patch()

        :param name: name of the function
        :param fn: - object of the function
        :returns: function -- decorated function
    """
    @functools.wraps(fn)
    def profile_cputime(*args, **kwarg):
        if not modules:
            getmodules()
        module = get_module_name(name)
        status = get_state(module)
        if status:
            st = time.time()
            rt = fn(*args, **kwarg)
            logger = logging.getLogger(module)
            logger.debug(_(' %(fn_name)s | %(time)f | ms'),
                {'fn_name': name,
                 'time': (time.time() - st) * 1000})
            return rt
        else:
            return fn(*args, **kwarg)

    return profile_cputime


def getmodules():
    if FLAGS.monkey_patch is True:
        for module_and_decorator in FLAGS.monkey_patch_modules:
            module = module_and_decorator.split(':')[0]
            modules.append(module)


def get_module_name(module_name):
    for m in modules:
        if module_name.startswith(m):
            return m


def add_module(module_name):
    if module_name is not None and module_name not in modules:
        modules.append(module_name)


def delete_module(module_name):
    if module_name is not None and module_name in modules:
        modules.remove(module_name)


def get_state(module_name):
    if not module_name:
        return False
    else:
        return True
