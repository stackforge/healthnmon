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


import sys
import pyclbr
import inspect
import logging
import traceback
from nova.openstack.common import importutils
from healthnmon import log
from healthnmon.profiler import profile_cpu, profile_mem

LOG = log.getLogger('healthnmon.utils')


def profile_cputime(module, decorator_name, status):
    try:
        if status:
            profile_cpu.add_module(module)
        else:
            profile_cpu.delete_module(module)

        # import decorator function
        decorator = importutils.import_class(decorator_name)
        __import__(module)
        # Retrieve module information using pyclbr
        module_data = pyclbr.readmodule_ex(module)
        for key in module_data.keys():
            # set the decorator for the class methods
            if isinstance(module_data[key], pyclbr.Class):
                clz = importutils.import_class("%s.%s" % (module, key))
                for method, func in inspect.getmembers(clz, inspect.ismethod):
                    if func.func_code.co_name == 'profile_cputime':
                        pass
                    else:
                        setattr(clz, method,
                                decorator("%s.%s.%s" % (module, key, method), func))
                        LOG.info(_('Decorated method ' + method))
            # set the decorator for the function
            if isinstance(module_data[key], pyclbr.Function):
                func = importutils.import_class("%s.%s" % (module, key))
                if func.func_code.co_name == 'profile_cputime':
                    pass
                else:
                    setattr(sys.modules[module], key,
                            decorator("%s.%s" % (module, key), func))
                    LOG.info(_('Decorated method ' + key))
    except:
        LOG.error(_('Invalid module or decorator name '))
        LOG.error(_('Exception occurred %s ') % traceback.format_exc())


def profile_memory(method, decorator_name, status, setref):
    try:
        profile_mem.modules_profiling_status[method] = status
        profile_mem.setref = setref
        # import decorator function
        decorator = importutils.import_class(decorator_name)
        class_str, _sep, method_str = method.rpartition('.')
        clz = importutils.import_class(class_str)
        # set the decorator for the function
        func = getattr(clz, method_str)
        if func.func_code.co_name == 'profile_memory':
            pass
        else:
            setattr(clz, method_str,
                    decorator(method, func))
            LOG.info(_('Decorated method ' + method_str))
    except:
        LOG.error(_('Invalid method or decorator name '))
        LOG.error(_('Exception occurred %s ') % traceback.format_exc())


def setLogLevel(level, module_name):
    level = level.upper()
    if level not in logging._levelNames:
        LOG.error(_(' Invalid log level %s ') % level)

    l = logging.getLevelName(level.upper())

    if module_name == 'healthnmon':
        logging.getLogger().setLevel(l)
        log.getLogger().logger.setLevel(l)
    else:
        log.getLogger(module_name).logger.setLevel(l)

    LOG.audit(_(module_name + ' log level set to %s ') % level)
