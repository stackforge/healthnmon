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
heathnmon Service default driver - Manage communication with compute nodes and collects inventory and monitoring info
"""

from nova import flags
from nova.openstack.common import importutils
from nova.openstack.common import cfg
from healthnmon import log as logging

LOG = logging.getLogger('healthnmon.driver')
driver_opts = [
cfg.StrOpt('healthnmon_inventory_manager',
            default='healthnmon.inventory_manager.InventoryManager',
            help='The healthnmon inventory manager class to use'),
    ]

FLAGS = flags.FLAGS
FLAGS.register_opts(driver_opts)


class Healthnmon(object):

    """The base class that all healthnmon classes should inherit from."""

    def __init__(self):
        self.inventory_manager = \
            importutils.import_object(FLAGS.healthnmon_inventory_manager)

    def get_compute_list(self):
        """Get a list of hosts from the InventoryManager."""

        return self.inventory_manager.get_compute_list()

    def poll_compute_nodes(self, context):
        """Poll child zones periodically to get status."""

        return self.inventory_manager.update(context)

    def poll_compute_perfmon(self, context):
        """Poll computes periodically to update performance data."""

        return self.inventory_manager.poll_perfmon(context)

    def get_resource_utilization(
        self,
        context,
        uuid,
        perfmon_type,
        window_minutes,
        ):
        """ Return performance data for requested host/vm for last windowMinutes."""

        return self.inventory_manager.get_resource_utilization(context,
                uuid, perfmon_type, window_minutes)
