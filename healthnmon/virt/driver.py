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
Driver base-classes:

    (Beginning of) the contract that compute inventory drivers must follow, and shared
    types that support that contract
"""


class ComputeInventoryDriver(object):

    """Base class for compute inventory drivers.
    """

    def init_rmcontext(self, compute_rmcontext):
        """Initialize anything that is necessary for the driver to function"""

        raise NotImplementedError()

    def get_host_ip_addr(self):
        """
        Retrieves the IP address of the dom0
        """

        raise NotImplementedError()

    def update_inventory(self, compute_id):
        """
        Updates the inventory details of VM Host, VMs, Network, Storage etc.,
        """

        raise NotImplementedError()

    def update_perfdata(self, uuid, perfmon_type):
        """
        Updates the performance data of VM Host, VMs.
        """

        raise NotImplementedError()

    def get_resource_utilization(
        self,
        uuid,
        perfmon_type,
        window_minutes,
    ):
        """
        Returns the performance data of VM Host, VMs for specified window minutes.
        """

        raise NotImplementedError()
