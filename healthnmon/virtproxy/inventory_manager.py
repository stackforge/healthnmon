# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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
Manage communication with compute nodes and
collects inventory and monitoring info
"""

from healthnmon.virtproxy.inventory_cache_manager import InventoryCacheManager
from nova.context import get_admin_context
from eventlet import greenpool
from healthnmon import rmcontext
from healthnmon.db import api
from healthnmon.virtproxy.virt import driver
from nova import db, utils
from healthnmon import utils as hnm_utils
from healthnmon import log as logging
from nova.openstack.common import rpc
from oslo.config import cfg
from nova.openstack.common import importutils
from nova.openstack.common import timeutils
from healthnmon.constants import Constants
from healthnmon.virtproxy.events import api as event_api
from healthnmon.virtproxy.events import event_metadata
import datetime
import traceback

invman_opts = [
    cfg.IntOpt('compute_db_check_interval',
               default=60,
               help='Interval for refresh of inventory from DB'),
    cfg.IntOpt('compute_failures_to_offline',
               default=3,
               help='Number of consecutive errors \
               before marking compute_node offline '),
    cfg.StrOpt('compute_inventory_driver',
               default='healthnmon.virtproxy.virt.connection',
               help='connection '),
    cfg.StrOpt('hypervisor_type',
               help='Hypervisor this virtproxy proxies to.\
               include: QEMU,'),
]
collector_opts = [
    cfg.StrOpt('healthnmon_collector_topic',
               default='healthnmon.collector',
               help='The topic used by healthnmon-collector'), ]
CONF = cfg.CONF
CONF.register_opts(invman_opts)
try:
    CONF.healthnmon_collector_topic
except cfg.NoSuchOptError:
    CONF.register_opts(collector_opts)

LOG = logging.getLogger(__name__)


class ComputeInventory(object):

    """Holds the compute node inventory for a particular compute node
    that is being managed in the zone."""

    def __init__(self, compute_rmcontext):
        self.is_active = True
        self.attempt = 0
        self.last_seen = datetime.datetime.min
        self.last_exception = None
        self.last_exception_time = None
        self.compute_rmcontext = compute_rmcontext
        self.compute_info = {}
        inventory_driver = \
            importutils.import_module(CONF.compute_inventory_driver)
        self.driver = \
            utils.check_isinstance(
                inventory_driver.get_connection(self.compute_rmcontext.rmType),
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
        return iscObj

    def get_compute_conn_driver(self):
        if self.driver is not None:
            return self.driver

    def log_error(self, exception):
        """Something went wrong. Check to see if compute_node should be
           marked as offline."""

        LOG.error(_('Exception occurred %s ') % exception)

        max_errors = CONF.compute_failures_to_offline
        self.attempt += 1
        if self.attempt >= max_errors:
            self.is_active = False
            LOG.error(_('No answer from compute_node \
            %(api_url)s after %(max_errors)d attempts. Marking inactive.')
                      % locals())

    def poll(self):
        """Eventlet worker to poll a self."""

        try:
            self.update_inventory()
        except Exception:
            self.log_error(traceback.format_exc())


class InventoryManager(object):

    def __init__(self, host=None):
        self.host_name = host
        self.last_compute_db_check = datetime.datetime.min
        self.green_pool = greenpool.GreenPool()
        self.perf_green_pool = greenpool.GreenPool()
        self._initCache()

    def _get_managed_vm_hosts(self, context=None, compute_ids=None):
        """ Query from DB the vm_hosts managed by this virtproxy instance
        """
        vmhosts = []
        if context is None:
            context = get_admin_context()
        if CONF.hypervisor_type and CONF.hypervisor_type.upper() in ("QEMU",
                                                                     "FAKE"):
            vmhosts = api.vm_host_get_all_by_filters(get_admin_context(),
                                                     {"deleted": False,
                                                      "virtualizationType":
                                                     CONF.hypervisor_type},
                                                     None, None)
        return vmhosts

    def _get_managed_compute_nodes(self, context=None):
        """ Query from DB the compute_nodes managed by this virtproxy instance
        """
        computes = []
        if context is None:
            context = get_admin_context()
        if CONF.hypervisor_type and CONF.hypervisor_type.upper()\
                in ("QEMU", "FAKE"):
            hypevisor_computes = []
            computes = db.compute_node_get_all(context)
            if computes:
                for compute in computes:
                    if compute['hypervisor_type'] == CONF.hypervisor_type:
                        hypevisor_computes.append(compute)
            computes = hypevisor_computes
        if computes is None:
            computes = []
        return computes

    def _add_compute_to_inventory(self, hypervisor_type, compute_id, host):
        LOG.info(_("Adding compute to inventory with id : %s") % compute_id)
        rm_context = rmcontext.ComputeRMContext(
            rmType=hypervisor_type,
            rmIpAddress=host,
            rmUserName='user',
            rmPassword='********')
        InventoryCacheManager.get_all_compute_inventory()[
            compute_id] = ComputeInventory(rm_context)

    def _refresh_from_db(self, context):
        """Make our compute_node inventory map match the db."""

        # Add/update existing compute_nodes ...

        computes = self._get_managed_compute_nodes(context)
        existing = InventoryCacheManager.get_all_compute_inventory().keys()
        db_keys = []
        for compute in computes:
            compute_id = str(compute['id'])
            service = compute['service']
            if service is not None:
                compute_alive = hnm_utils.is_service_alive(
                    service['updated_at'], service['created_at'])
                db_keys.append(compute_id)
                if not compute_alive:
                    LOG.warn(_('Service %s for host %s is not active') % (
                        service['binary'], service['host']))
#                    continue
                if compute_id not in existing:
                    self._add_compute_to_inventory(compute[
                                                   'hypervisor_type'],
                                                   compute_id, service['host'])
                    LOG.audit(_(
                        'New Host with compute_id  %s is \
                        obtained') % (compute_id))
                InventoryCacheManager.get_all_compute_inventory()[
                    compute_id].update_compute_Id(compute_id)
            else:
                LOG.warn(_(
                    ' No services entry found for compute id  \
                    %s') % compute_id)

        # Cleanup compute_nodes removed from db ...
        self._clean_deleted_computes(db_keys)

    def _clean_deleted_computes(self, db_keys):
        keys = InventoryCacheManager.get_all_compute_inventory(
        ).keys()  # since we're deleting
        deletion_list = []
        for compute_id in keys:
            if compute_id not in db_keys:
                vmHostObj = InventoryCacheManager.get_all_compute_inventory()[
                    compute_id].get_compute_info()
                if vmHostObj is not None:
                    deletion_list.append(vmHostObj.get_id())

        host_deleted_list = []
        if len(deletion_list) != 0:
            # Delete object from cache
            for _id in deletion_list:
                host_deleted = InventoryCacheManager.get_object_from_cache(
                    _id, Constants.VmHost)
                if host_deleted is not None:
                    host_deleted_list.append(
                        InventoryCacheManager.
                        get_object_from_cache(_id, Constants.VmHost))
                else:
                    LOG.warn(_(
                        "VmHost object for id %s not found in cache") % _id)

            # Delete the VmHost from DB
            api.vm_host_delete_by_ids(get_admin_context(), deletion_list)
            # Generate the VmHost Removed Event
            for host_deleted in host_deleted_list:
                LOG.debug(_('Generating Host Removed event for the \
                host id : %s') % str(
                    host_deleted.get_id()))
                event_api.notify_host_update(
                    event_metadata.EVENT_TYPE_HOST_REMOVED, host_deleted)
                # VmHost is deleted from compute inventory and inventory cache
                # after notifying the event
                del InventoryCacheManager.get_all_compute_inventory()[
                    host_deleted.get_id()]
                InventoryCacheManager.delete_object_in_cache(
                    host_deleted.get_id(), Constants.VmHost)
                LOG.audit(_('Host with (UUID, host name) - (%s, %s) \
                got removed') % (
                    host_deleted.get_id(), host_deleted.get_name()))

    def get_compute_list(self):
        """Return the list of nova-compute_nodes we know about."""

        return [compute.get_compute_info() for compute in
                InventoryCacheManager.get_all_compute_inventory().values()]

    def _poll_computes(self):
        """Try to connect to each compute node and get update."""

        def _worker(compute_inventory):
            compute_inventory.poll()

        for compute in InventoryCacheManager.\
                get_all_compute_inventory().values():
            self.green_pool.spawn_n(_worker, compute)
            LOG.debug(_('Free threads available in green pool %d ')
                      % self.green_pool.free())

    def update(self, context):
        """Update status for all compute_nodes.  This should be called
        periodically to refresh the compute_node inventory.
        """
        self.green_pool.waitall()
        diff = timeutils.utcnow() - self.last_compute_db_check
        if diff.seconds >= CONF.compute_db_check_interval:
            LOG.info(_('Updating compute_node cache from db.'))
            self.last_compute_db_check = timeutils.utcnow()
            self._refresh_from_db(context)
        self._poll_computes()

    def _initCache(self):

        # Read from DB all the vmHost objects and populate
        # the cache for each IP if cache is empty

        LOG.info(_('Entering into initCache'))
        computes = self._get_managed_compute_nodes()
        compute_ids = []
        for compute in computes:
            compute_id = str(compute['id'])
            compute_ids.append(compute_id)
            service = compute['service']
            self._add_compute_to_inventory(compute[
                                           'hypervisor_type'],
                                           compute_id, service['host'])
        vmhosts = self._get_managed_vm_hosts(compute_ids)
        vmhost_ids = []
        storagevolume_ids = []
        subnet_ids = []
        for vmhost in vmhosts:
            vmhost_ids.append(vmhost.get_id())
            storagevolume_ids.extend(vmhost.get_storageVolumeIds())
            for virtualswitch in vmhost.get_virtualSwitches():
                subnet_ids.extend(virtualswitch.get_subnetIds())
        vms = api.vm_get_all_by_filters(get_admin_context(),
                                        {"deleted": False,
                                         "vmHostId": vmhost_ids},
                                        None, None)
        storageVolumes = api.storage_volume_get_by_ids(get_admin_context(),
                                                       storagevolume_ids)
        subNets = api.subnet_get_by_ids(get_admin_context(), subnet_ids)

        self._updateInventory(vmhosts)
        self._updateInventory(vms)
        self._updateInventory(storageVolumes)
        self._updateInventory(subNets)

        LOG.info(_('Hosts obtained from db: %s') % str(len(vmhosts)))
        LOG.info(_('Vms obtained from db: %s') % str(len(vms)))
        LOG.info(_('Storage volumes obtained from db: %s') %
                 str(len(storageVolumes)))
        LOG.info(_('Subnets obtained from db: %s') % str(len(subNets)))

        LOG.info(_('Completed the initCache method'))

    def _updateInventory(self, objlist):
        if objlist is not None:
            for obj in objlist:
                InventoryCacheManager.update_object_in_cache(obj.id, obj)

    def poll_perfmon(self, context):
        """ Periodically polls to refresh the performance data
        of VmHost and Vm in inventory """
        LOG.info(
            _('Polling performance data periodically for Vmhosts and Vms'))

        def _worker(uuid, conn_driver, perfmon_type):
            conn_driver.update_perfdata(uuid, perfmon_type)
            # Update data to collector
            method = None
            if perfmon_type == Constants.VmHost:
                method = 'update_vmhost_utilization'
            elif perfmon_type == Constants.Vm:
                method = 'update_vm_utilization'
            if method:
                utilization = conn_driver\
                    .get_resource_utilization(uuid, perfmon_type, 5)
                rpc.cast(context,
                         CONF.healthnmon_collector_topic,
                         {'method': method,
                          'args': {'uuid': uuid,
                                   'utilization': utilization.__dict__}})

        for host_id in InventoryCacheManager.\
                get_inventory_cache()[Constants.VmHost].keys():
            conn_driver = InventoryCacheManager.get_compute_conn_driver(
                host_id,
                Constants.VmHost)
            if conn_driver is not None:
                self.perf_green_pool.spawn_n(_worker, host_id,
                                             conn_driver, Constants.VmHost)
            else:
                LOG.error(_('Error in monitoring performance data for Host %s '
                            ) % host_id)
            host_obj = InventoryCacheManager.get_inventory_cache(
            )[Constants.VmHost][host_id]
            for vm_id in host_obj.get_virtualMachineIds():
                vm_obj = InventoryCacheManager.get_object_from_cache(
                    vm_id, Constants.Vm)
                if vm_obj.get_powerState() \
                        == Constants.VM_POWER_STATES[1]:
                    conn_driver = InventoryCacheManager.\
                        get_compute_conn_driver(vm_id, Constants.Vm)
                    if conn_driver is not None:
                        self.perf_green_pool.spawn_n(_worker, vm_id,
                                                     conn_driver, Constants.Vm)
                    else:
                        LOG.error(_('Error in monitoring performance \
                        data for VM %s ') % vm_id)

    def get_resource_utilization(
        self,
        context,
        uuid,
        perfmon_type,
        window_minutes,
    ):
        """ Returns performance data of VMHost and VM via
        hypervisor connection driver """

        return InventoryCacheManager.get_compute_conn_driver(
            uuid, perfmon_type).get_resource_utilization(uuid,
                                                         perfmon_type,
                                                         window_minutes)
