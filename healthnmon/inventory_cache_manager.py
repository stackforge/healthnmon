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
Inventory cache manager
"""
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    Vm, StorageVolume, Subnet
from healthnmon.constants import Constants
from healthnmon import log

LOG = log.getLogger(__name__)


class InventoryCacheManager(object):

    """Keeps the compute_node Inventory updated."""

    global _inventoryCache
    global _compute_inventory

    _inventoryCache = {
        Constants.VmHost: {},
        Constants.Vm: {},
        Constants.StorageVolume: {},
        Constants.Network: {},
        }
    _compute_inventory = {}  # {<compute_Id> : ComputeInventory }

    @staticmethod
    def get_inventory_cache():
        return _inventoryCache

    @staticmethod
    def get_all_compute_inventory():
        return _compute_inventory

    @staticmethod
    def get_object_from_cache(uuid, obj_type):
        LOG.debug(_(' Entering into get_object_from_cache for uuid %s ')
                  % uuid)
        if uuid in InventoryCacheManager.get_inventory_cache()[obj_type]:
            return InventoryCacheManager.get_inventory_cache()[obj_type][uuid]

    @staticmethod
    def update_object_in_cache(uuid, obj):
        LOG.debug(_(' Entering into update_object_in_cache for uuid %s')
                  % uuid)
        if isinstance(obj, VmHost):
            InventoryCacheManager.get_inventory_cache()[Constants.VmHost][uuid] = \
                obj
        elif isinstance(obj, Vm):
            InventoryCacheManager.get_inventory_cache()[Constants.Vm][uuid] = obj
        elif isinstance(obj, StorageVolume):
            InventoryCacheManager.get_inventory_cache()[Constants.StorageVolume][uuid] = \
                obj
        elif isinstance(obj, Subnet):
            InventoryCacheManager.get_inventory_cache()[Constants.Network][uuid] = \
                obj
        LOG.debug(_(' Exiting from update_object_in_cache for uuid %s')
                  % uuid)

    @staticmethod
    def delete_object_in_cache(uuid, obj_type):
        LOG.debug(_(' Entering into delete_object_in_cache for uuid = %s')
                  % uuid)
        if uuid in InventoryCacheManager.get_inventory_cache()[obj_type]:
            del InventoryCacheManager.get_inventory_cache()[obj_type][uuid]
        LOG.debug(_(' Exiting from delete_object_in_cache for uuid %s')
                  % uuid)

    @staticmethod
    def get_compute_inventory(compute_id):
        if compute_id in InventoryCacheManager.get_all_compute_inventory():
            return InventoryCacheManager.get_all_compute_inventory().get(compute_id)

    @staticmethod
    def get_compute_conn_driver(uuid, obj_type):
        """ Returns the connection driver for VmHost/Vm in inventory """

        inv_obj = InventoryCacheManager.get_object_from_cache(uuid, obj_type)
        if obj_type == Constants.VmHost:
            compute_id = inv_obj.get_id()
        elif obj_type == Constants.Vm:
            host_id = inv_obj.get_vmHostId()
            compute_id = InventoryCacheManager.get_object_from_cache(host_id,
                    Constants.VmHost).get_id()

        compute_inv = InventoryCacheManager.get_compute_inventory(compute_id)
        if compute_inv is not None:
            return InventoryCacheManager.get_compute_inventory(compute_id).get_compute_conn_driver()
