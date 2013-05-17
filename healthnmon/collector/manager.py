# vim: tabstop=4 shiftwidth=4 softtabstop=4

#          (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
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
heathnmon Service - Manage communication with compute nodes and
collects inventory and monitoring info
"""

from nova import manager, utils
from nova.openstack.common import importutils
from nova.openstack.common import cfg
from healthnmon.constants import Constants
from healthnmon.collector import driver
from healthnmon import log as logging
from nova import exception
import sys

LOG = logging.getLogger(__name__)

manager_opts = [
    cfg.StrOpt('healthnmon_driver',
               default='healthnmon.collector.driver.Healthnmon',
               help='Default driver to use for the healthnmon service')
]

CONF = cfg.CONF


def register_flags():
    try:
        CONF.healthnmon_driver
    except cfg.NoSuchOptError:
        CONF.register_opts(manager_opts)

register_flags()


class HealthnMonCollectorManager(manager.Manager):

    """Manage communication with compute nodes, collects inventory
    and monitoring info."""

    def __init__(
        self,
        host=None,
        healthnmon_driver=None,
        *args,
        **kwargs
    ):
        self.host_name = host
        if not healthnmon_driver:
            healthnmon_driver = CONF.healthnmon_driver
        LOG.info(
            "Initializing healthnmon. Loading driver %s" % healthnmon_driver)
        try:
            self.driver = \
                utils.check_isinstance(
                    importutils.import_object(
                        healthnmon_driver, host=self.host_name),
                    driver.Healthnmon)
        except ImportError, e:
            LOG.error(_('Unable to load the healthnmon driver: %s') % e)
            sys.exit(1)
        except exception.ClassNotFound, e:
            LOG.error(_('Unable to load the healthnmon driver: %s') % e)
            sys.exit(1)

        super(HealthnMonCollectorManager, self).__init__(*args, **kwargs)

    def get_vmhost_utilization(
        self,
        context,
        uuid,
        windowMinutes=5,
    ):
        """ Gets sampled performance data of requested VmHost """

        LOG.info(_('Received the message for VM Host ' +
                   'Utilization for uuid : %s') % uuid)
        resource_utilization = \
            self.driver.get_resource_utilization(context,
                                                 uuid,
                                                 Constants.VmHost,
                                                 windowMinutes)
        LOG.debug(_('VM Host Resource Utilization: %s')
                  % resource_utilization)
        return dict(ResourceUtilization=resource_utilization)

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
        LOG.debug(_('VM Resource Utilization : %s')
                  % resource_utilization)
        return dict(ResourceUtilization=resource_utilization)

    def update_vmhost_utilization(
        self,
        context,
        uuid,
        utilization,
    ):
        """ Updates sampled performance data of VmHost to collector cache """

        LOG.info(_('Received the message for VM Host ' +
                   'Utilization update for uuid : %s') % uuid)
        self.driver.update_resource_utilization(context,
                                                uuid,
                                                Constants.VmHost,
                                                utilization)

    def update_vm_utilization(
        self,
        context,
        uuid,
        utilization,
    ):
        """ Updates sampled performance data of Vm to collector cache """

        LOG.info(_('Received the message for VM ' +
                   'Utilization update for uuid : %s'), uuid)
        self.driver.update_resource_utilization(
            context, uuid, Constants.Vm, utilization)
