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
heathnmon Service default driver - Manage communication with
compute nodes and collects inventory and monitoring info
"""

from nova.openstack.common import cfg
from nova.openstack.common import importutils
from healthnmon import log as logging

LOG = logging.getLogger(__name__)
driver_opts = [
    cfg.StrOpt('healthnmon_collector_impl',
               default=
               'healthnmon.collector.collector_manager.CollectorManager',
               help='The healthnmon inventory manager class to use'),
]

CONF = cfg.CONF
CONF.register_opts(driver_opts)


class Healthnmon(object):

    """The base class that all healthnmon
     driver classes should inherit from.
    """

    def __init__(self, host=None):
        self.host_name = host
        self.collector_manager = \
            importutils.import_object(
                CONF.healthnmon_collector_impl, host=self.host_name)

    def get_resource_utilization(
        self,
        context,
        uuid,
        perfmon_type,
        window_minutes,
    ):
        """ Return performance data for requested host/vm
        for last windowMinutes."""

        return self.collector_manager.get_resource_utilization(
            context,
            uuid, perfmon_type, window_minutes)

    def update_resource_utilization(
        self,
        context,
        uuid,
        perfmon_type,
        utilization,
    ):
        """ Updates sampled performance data to collector cache """
        return self.collector_manager.update_resource_utilization(
            context,
            uuid, perfmon_type, utilization)
