# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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

from healthnmon.constants import Constants
from healthnmon import log

LOG = log.getLogger(__name__)


class UtilizationCacheManager(object):
    global _utilizationCache

    _utilizationCache = {
        Constants.VmHost: {},
        Constants.Vm: {},
    }

    @staticmethod
    def get_utilization_cache():
        return _utilizationCache

    @staticmethod
    def get_utilization_from_cache(uuid, obj_type):
        LOG.debug(
            _('Entering into get_utilization_from_cache ' +
              'for uuid:obj_type %s:%s'), uuid, obj_type)
        if uuid in UtilizationCacheManager.get_utilization_cache()[obj_type]:
            return UtilizationCacheManager.\
                get_utilization_cache()[obj_type][uuid]

    @staticmethod
    def update_utilization_in_cache(uuid, obj_type, utilization):
        LOG.debug(
            _('Entering into update_utilization_in_cache ' +
              'for uuid:obj_type %s:%s'), uuid, obj_type)
        UtilizationCacheManager.\
            get_utilization_cache()[obj_type][uuid] = utilization

    @staticmethod
    def delete_utilization_in_cache(uuid, obj_type):
        LOG.debug(
            _('Entering into delete_utilization_in_cache ' +
              'for uuid:obj_type %s:%s'), uuid, obj_type)
        if uuid in UtilizationCacheManager.get_utilization_cache()[obj_type]:
            del UtilizationCacheManager.\
                get_utilization_cache()[obj_type][uuid]
