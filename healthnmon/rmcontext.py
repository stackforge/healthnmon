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
heathnmon - Context details of Resource manager managing the Compute node
"""

from healthnmon import log as logging

LOG = logging.getLogger('healthnmon.driver')


class ComputeRMContext(object):

    """Holds the compute node context for a particular compute
    node that is being managed in the zone."""

    def __init__(
        self,
        rmType=None,
        rmIpAddress=None,
        rmUserName=None,
        rmPassword=None,
        rmPort=None,
    ):
        self.rmType = rmType
        self.rmIpAddress = rmIpAddress
        self.rmUserName = rmUserName
        self.rmPassword = rmPassword
        self.rmPort = rmPort

    def __getattribute__(self, name):
        try:
            return super(ComputeRMContext, self).__getattribute__(name)
        except AttributeError, ex:
            raise ex

    def __eq__(self, other):
        return self.rmIpAddress == other.rmIpAddress

    def __hash__(self):
        return hash(self.rmIpAddress)
