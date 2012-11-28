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

"""Common utility methods for events module
"""

from healthnmon.resourcemodel.healthnmonResourceModel import Vm, \
    PortGroup
from healthnmon import log

LOG = log.getLogger('healthnmon.events.util')

# Properties of different resource model types for which updated event is ignored

ignoredProperties = {Vm: [
    'connectionState',
    'powerState',
    'cpuResourceAllocation',
    'memoryResourceAllocation',
    'processorSpeedMhz',
    'processorSpeedTotalMhz',
    'memoryConsumed',
    'processorLoadPercent',
    'utilization',
    'limits',
    'createEpoch',
    'lastModifiedEpoch',
    'deletedEpoch',
    'deleted',
], PortGroup: [
    'utilization',
    'limits',
    'createEpoch',
    'lastModifiedEpoch',
    'deletedEpoch',
    'deleted',
]}


def getChangedAttributesForUpdateEvent(obj, resourcemodel_diff_res):
    """Get the list of changed attributes that could trigger a update event
    """

    if obj is None or resourcemodel_diff_res is None:
        return []
    if not obj.__class__ in ignoredProperties:
        LOG.debug(_('Attributes for triggering Update event for '
                  + repr(obj.__class__) + ' not configured'))
        return []
    ignoredProps = ignoredProperties.get(obj.__class__)
    result = []
    for diff_key in resourcemodel_diff_res.keys():
        diff_res = resourcemodel_diff_res[diff_key]
        for changed_attr in diff_res.keys():
            if changed_attr not in ignoredProps:
                result.append(changed_attr)
    return result
