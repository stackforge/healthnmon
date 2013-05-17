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
Manage communication with compute nodes and
collects inventory and monitoring info
"""

from healthnmon import log as logging
from healthnmon.collector.utilization_cache_manager import \
    UtilizationCacheManager

LOG = logging.getLogger(__name__)


class CollectorManager(object):
    def __init__(self, host=None):
        self.host_name = host

    def get_resource_utilization(
        self,
        context,
        uuid,
        perfmon_type,
        window_minutes,
    ):
        """ Returns performance data of VMHost and VM via
        hypervisor connection driver """
        return UtilizationCacheManager.get_utilization_from_cache(
            uuid,
            perfmon_type
        )

    def update_resource_utilization(
        self,
        context,
        uuid,
        perfmon_type,
        utilization,
    ):
        """ Updates sampled performance data to collector cache """
        UtilizationCacheManager.update_utilization_in_cache(
            uuid, perfmon_type, utilization)
