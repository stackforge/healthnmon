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
Manage communication with compute nodes and collects inventory and monitoring info
"""

from healthnmon.inventory_cache_manager import InventoryCacheManager
from nova.context import get_admin_context
from eventlet import greenpool
from healthnmon import rmcontext
from healthnmon.db import api
from healthnmon.virt import driver
from nova import db, flags, utils
from healthnmon import utils as hnm_utils
from healthnmon import log as logging
from nova.openstack.common import cfg
from nova.openstack.common import importutils
from nova.openstack.common import timeutils
#from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
#    Vm, StorageVolume, Subnet
from healthnmon.constants import Constants
from healthnmon.events import api as event_api
from healthnmon.events import event_metadata
import datetime
import traceback

invman_opts = [
cfg.IntOpt('compute_db_check_interval',
            default=60,
            help='Interval for refresh of inventory from DB'),
cfg.IntOpt('compute_failures_to_offline',
            default=3,
            help='Number of consecutive errors before marking compute_node offline '),
cfg.StrOpt('_compute_inventory_driver',
            default='healthnmon.virt.connection',
            help='connection ')
    ]
FLAGS = flags.FLAGS
FLAGS.register_opts(invman_opts)

LOG = logging.getLogger('healthnmon.inventory_manager')


class ComputeInventory(object):

    """Holds the compute node inventory for a particular compute node that is being managed in the zone."""

    def __init__(self, compute_rmcontext):
        self.is_active = True
        self.attempt = 0
        self.last_seen = datetime.datetime.min
        self.last_exception = None
        self.last_exception_time = None
        self.compute_rmcontext = compute_rmcontext
        self.compute_info = {}
        inventory_driver = \
            importutils.import_module(FLAGS._compute_inventory_driver)
        self.driver = \
            utils.check_isinstance(inventory_driver.get_connection(self.compute_rmcontext.rmType),
                                   driver.ComputeInventoryDriver)
        self.driver.init_rmcontext(compute_rmcontext)
        self.compute_id = None

    def update_compute_info(self, rmContext, invobject):
        """Update invobject details """

        self.compute_info[rmContext] = invobject

    def update_compute_Id(self, compute_id):
        self.compute_id = compute_id

    def update_inventory(self):
        """Update compute_node inventory after successful communications with
       compute_node."""

        self.last_seen = timeutils.utcnow()
        self.attempt = 0
        self.is_active = True
        self.driver.update_inventory(self.compute_id)

    def get_compute_info(self):
        iscObj = \
            self.compute_info.get(self.compute_rmcontext)
#        if iscObj != None:
#            return iscObj
        return iscObj
#        return None

    def get_compute_conn_driver(self):
        if self.driver != None:
            return self.driver

    def log_error(self, exception):
        """Something went wrong. Check to see if compute_node should be
           marked as offline."""

        LOG.error(_('Exception occurred %s ') % exception)

        max_errors = FLAGS.compute_failures_to_offline
        self.attempt += 1
        if self.attempt >= max_errors:
            self.is_active = False
            LOG.error(_('No answer from compute_node %(api_url)s after %(max_errors)d attempts. Marking inactive.'
                      ) % locals())

    def poll(self):
        """Eventlet worker to poll a self."""

        try:
            self.update_inventory()
        except Exception:
            self.log_error(traceback.format_exc())


class InventoryManager(object):

    def __init__(self):
        self.last_compute_db_check = datetime.datetime.min
        self.green_pool = greenpool.GreenPool()
        self.perf_green_pool = greenpool.GreenPool()
        self._initCache()

    def _refresh_from_db(self, context):
        """Make our compute_node inventory map match the db."""

        # Add/update existing compute_nodes ...

        computes = db.compute_node_get_all(context)
        existing = InventoryCacheManager.get_all_compute_inventory().keys()
        db_keys = []
        for compute in computes:
            compute_id = str(compute['id'])
            service = compute['service']
            if service is not None:
                compute_alive = hnm_utils.is_service_alive(service['updated_at'], service['created_at'])
                db_keys.append(compute_id)
                if not compute_alive:
                    LOG.warn(_('Service %s for host %s is not active') % (service['binary'], service['host']))
                    continue
                if compute_id not in existing:
                    rm_context = \
                        rmcontext.ComputeRMContext(rmType=compute['hypervisor_type'
                            ], rmIpAddress=service['host'],
                            rmUserName='user', rmPassword='********')
                    InventoryCacheManager.get_all_compute_inventory()[compute_id] = \
                        ComputeInventory(rm_context)
                    LOG.audit(
                    _('New Host with compute_id  %s is obtained') % (compute_id))
                InventoryCacheManager.get_all_compute_inventory()[compute_id].update_compute_Id(compute_id)
            else:
                LOG.warn(_(' No services entry found for compute id  %s') % compute_id)

        # Cleanup compute_nodes removed from db ...

        keys = InventoryCacheManager.get_all_compute_inventory().keys()  # since we're deleting
        deletion_list = []
        for compute_id in keys:
            if compute_id not in db_keys:
                vmHostObj = InventoryCacheManager.get_all_compute_inventory()[compute_id].get_compute_info()
                if vmHostObj != None:
                    deletion_list.append(vmHostObj.get_id())

        host_deleted_list = []
        if len(deletion_list) != 0:
            # Delete object from cache
            for _id in deletion_list:
                host_deleted = InventoryCacheManager.get_object_from_cache(_id,
                    Constants.VmHost)
                if host_deleted is not None:
                    host_deleted_list.append(InventoryCacheManager.get_object_from_cache(_id, Constants.VmHost))
                else:
                    LOG.warn(_("VmHost object for id %s not found in cache") % _id)

            # Delete the VmHost from DB
            api.vm_host_delete_by_ids(get_admin_context(), deletion_list)
            # Generate the VmHost Removed Event
            for host_deleted in host_deleted_list:
                LOG.debug(_('Generating Host Removed event for the host id : %s') % str(host_deleted.get_id()))
                event_api.notify_host_update(event_metadata.EVENT_TYPE_HOST_REMOVED, host_deleted)
                # VmHost is deleted from compute inventory and inventory cache after notifying the event
                del InventoryCacheManager.get_all_compute_inventory()[host_deleted.get_id()]
                InventoryCacheManager.delete_object_in_cache(host_deleted.get_id(), Constants.VmHost)
                LOG.audit(_('Host with (UUID, host name) - (%s, %s) got removed') % (host_deleted.get_id(), host_deleted.get_name()))

    def get_compute_list(self):
        """Return the list of nova-compute_nodes we know about."""

        return [compute.get_compute_info() for compute in
                InventoryCacheManager.get_all_compute_inventory().values()]

    def _poll_computes(self):
        """Try to connect to each compute node and get update."""

        def _worker(compute_inventory):
            compute_inventory.poll()

        for compute in InventoryCacheManager.get_all_compute_inventory().values():
            self.green_pool.spawn_n(_worker, compute)
            LOG.debug(_('Free threads available in green pool %d ')
                      % self.green_pool.free())

    def update(self, context):
        """Update status for all compute_nodes.  This should be called
        periodically to refresh the compute_node inventory.
        """
        self.green_pool.waitall()
        diff = timeutils.utcnow() - self.last_compute_db_check
        if diff.seconds >= FLAGS.compute_db_check_interval:
            LOG.info(_('Updating compute_node cache from db.'))
            self.last_compute_db_check = timeutils.utcnow()
            self._refresh_from_db(context)
        self._poll_computes()

    def _initCache(self):

        # Read from DB all the vmHost objects and populate the cache for each IP if cache is empty

        LOG.info(_(' Entering into initCache'))
        vmhosts = api.vm_host_get_all(get_admin_context())
        vms = api.vm_get_all(get_admin_context())
        storageVolumes = api.storage_volume_get_all(get_admin_context())
        subNets = api.subnet_get_all(get_admin_context())
        self._updateInventory(vmhosts)
        self._updateInventory(vms)
        self._updateInventory(storageVolumes)
        self._updateInventory(subNets)

        LOG.info(_('Hosts obtained from db ') % vmhosts)
        LOG.info(_('Vms obtained from db ') % vms)
        LOG.info(_('Storage volumes obtained from db ')
                  % storageVolumes)

        LOG.info(_('Completed the initCache method'))

    def _updateInventory(self, objlist):
        if objlist != None:
            for obj in objlist:
                InventoryCacheManager.update_object_in_cache(obj.id, obj)

    def poll_perfmon(self, context):
        """ Periodically polls to refresh the performance data of VmHost and Vm in inventory """
        LOG.info(_('Polling performance data periodically for Vmhosts and Vms'))

        def _worker(uuid, conn_driver, perfmon_type):
            conn_driver.update_perfdata(uuid, perfmon_type)

        for host_id in InventoryCacheManager.get_inventory_cache()[Constants.VmHost].keys():
            conn_driver = InventoryCacheManager.get_compute_conn_driver(host_id,
                    Constants.VmHost)
            if conn_driver is not None:
                self.perf_green_pool.spawn_n(_worker, host_id,
                        conn_driver, Constants.VmHost)
            else:
                LOG.error(_('Error in monitoring performance data for Host %s '
                          ) % host_id)
            host_obj = InventoryCacheManager.get_inventory_cache()[Constants.VmHost][host_id]
            for vm_id in host_obj.get_virtualMachineIds():
                vm_obj = InventoryCacheManager.get_object_from_cache(vm_id, Constants.Vm)
                if vm_obj.get_powerState() \
                    == Constants.VM_POWER_STATES[1]:
                    conn_driver = InventoryCacheManager.get_compute_conn_driver(vm_id,
                            Constants.Vm)
                    if conn_driver is not None:
                        self.perf_green_pool.spawn_n(_worker, vm_id,
                                conn_driver, Constants.Vm)
                    else:
                        LOG.error(_('Error in monitoring performance data for VM %s '
                                  ) % vm_id)

    def get_resource_utilization(
        self,
        context,
        uuid,
        perfmon_type,
        window_minutes,
        ):
        """ Returns performance data of VMHost and VM via hypervisor connection driver """

        return InventoryCacheManager.get_compute_conn_driver(uuid,
                perfmon_type).get_resource_utilization(uuid,
                perfmon_type, window_minutes)
