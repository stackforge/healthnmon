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
heathnmon Service - Manage communication with compute nodes and collects inventory and monitoring info
"""

from nova import flags, manager, utils
from healthnmon.profiler import helper
from nova.openstack.common import cfg
from healthnmon.constants import Constants
from healthnmon import driver
from healthnmon import log as logging
from nova import exception
import sys

LOG = logging.getLogger('healthnmon.manager')

manager_opts = [
cfg.StrOpt('healthnmon_driver',
            default='healthnmon.driver.Healthnmon',
            help='Default driver to use for the healthnmon service')
    ]

perfmon_opts = [
cfg.IntOpt("perfmon_refresh_interval",
            default=300,
            help="performance data refresh period.")
    ]

topic_opts = [
cfg.StrOpt('healthnmon_topic',
            default='healthnmon',
            help='the topic healthnmon service listen on')
    ]

FLAGS = flags.FLAGS


def register_flags():
    try:
        FLAGS.healthnmon_driver
    except cfg.NoSuchOptError:
        FLAGS.register_opts(manager_opts)
    try:
        FLAGS.perfmon_refresh_interval
    except cfg.NoSuchOptError:
        FLAGS.register_opts(perfmon_opts)
    try:
        FLAGS.healthnmon_topic
    except cfg.NoSuchOptError:
        FLAGS.register_opts(topic_opts)

register_flags()


class HealthnMonManager(manager.Manager):

    """Manage communication with compute nodes, collects inventory and monitoring info."""

    def __init__(
        self,
        healthnmon_driver=None,
        *args,
        **kwargs
        ):
        if not healthnmon_driver:
            healthnmon_driver = FLAGS.healthnmon_driver
        LOG.info("Initializing healthnmon. Loading driver %s" % healthnmon_driver)
        try:
            self.driver = \
                utils.check_isinstance(utils.import_object(healthnmon_driver),
                    driver.Healthnmon)
        except exception.ClassNotFound, e:
            LOG.error(_('Unable to load the healthnmon driver: %s') % e)
            sys.exit(1)

        super(HealthnMonManager, self).__init__(*args, **kwargs)

    @manager.periodic_task
    def _poll_compute_nodes(self, context):
        """Poll compute nodes periodically to refresh inventory details."""

        self.driver.poll_compute_nodes(context)

    def get_compute_list(self):
        """Get a list of hosts from the HostManager."""

        return self.driver.get_compute_list()

    @manager.periodic_task(ticks_between_runs=FLAGS.perfmon_refresh_interval
                           / 60 - 1)
    def _poll_compute_perfmon(self, context):
        """Poll compute nodes periodically to refresh performance data details."""

        self.driver.poll_compute_perfmon(context)

    def get_vmhost_utilization(
        self,
        context,
        uuid,
        windowMinutes=5,
        ):
        """ Gets sampled performance data of requested VmHost """

        LOG.info(_('Received the message for VM Host Utilization for uuid : %s'
                 ) % uuid)
        resource_utilization = \
            self.driver.get_resource_utilization(context, uuid,
                Constants.VmHost, windowMinutes)
        LOG.info(_('VM Host Resource Utilization: %s')
                 % resource_utilization.__dict__)
        return dict(ResourceUtilization=resource_utilization.__dict__)

    def get_vm_utilization(
        self,
        context,
        uuid,
        windowMinutes=5,
        ):
        """ Gets sampled performance data of requested Vm """

        LOG.info(_('Received the message for VM Utilization for uuid : %s'
                 ) % uuid)
        resource_utilization = \
            self.driver.get_resource_utilization(context, uuid,
                Constants.Vm, windowMinutes)
        LOG.info(_('VM Resource Utilization : %s')
                 % resource_utilization.__dict__)
        return dict(ResourceUtilization=resource_utilization.__dict__)

    def profile_cputime(self, context, module, decorator, status):
        LOG.info(_('Received the message for enabling/disabling cputime profiling for module %s'), module)

        helper.profile_cputime(module, decorator, status)

    def profile_memory(self, context, method, decorator, status, setref):
        LOG.info(_('Received the message for enabling/disabling memory profiling for method %s '), method)

        helper.profile_memory(method, decorator, status, setref)

    def setLogLevel(self, context, level, module):
        LOG.info(_('Received the message for setting log level for %s '), module)

        helper.setLogLevel(level, module)
