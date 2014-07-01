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

"""Event generator module
    Generates events by by calling healthnmon notifier
"""

from healthnmon.virtproxy.inventory_cache_manager import InventoryCacheManager
from healthnmon.virtproxy.events import event_metadata, payload_generator
from healthnmon.constants import Constants
from healthnmon.notifier import api as notifier_api
from nova import context
from nova.db import api as nova_db
from healthnmon import log

LOG = log.getLogger('healthnmon.virtproxy.events.api')


def notify(event_type, obj, **kwargs):
    """Generate event for a event type id
    This API is used by the different healthnmon modules
    which need to generate event.

            Parameters:
                event_type - One of the event types declared
                in healthnmon.events.event_meta_data
                obj - Vm, VmHost or StorageVolume object
                for which this event is to be generated
    """

    eventmetadata_obj = event_metadata.get_EventMetaData(event_type)
    payload = payload_generator.generate_payload(eventmetadata_obj,
                                                 obj, **kwargs)

    # Set publisher_id as <nova-scheduler-service.host>.healthnmon

    publisher_id = None
    admin_ctxt = context.get_admin_context()
    scheduler_services = None
    try:
        scheduler_services = \
            nova_db.service_get_all_by_topic(admin_ctxt, 'scheduler')
    except:
        LOG.error(_('Could not fetch scheduler service from nova db'))
    if scheduler_services is None or len(scheduler_services) < 1:
        LOG.debug(_('Scheduler service not found.'))
    else:
        if len(scheduler_services) > 1:
            LOG.debug(_('More than 1 entry for Scheduler service found.'
                        ))
        scheduler_service = scheduler_services[0]
        scheduler_service_host = scheduler_service['host']
        if scheduler_service_host is None \
                or len(scheduler_service_host) < 1:
            LOG.debug(_('Invalid host name for Scheduler service entry : '
                        + str(scheduler_service_host)))
        else:
            publisher_id = scheduler_service_host + '.' + 'healthnmon'
    if publisher_id is None:
        publisher_id = 'healthnmon'
        LOG.warn(_('Could not determine host name of nova scheduler service. \
        Using default publisher id %s'
                   % publisher_id))

    # Send message to notifier api
    LOG.debug(_('Sending notification with publisher_id: %s, name: %s,\
    payload: %s')
              % (publisher_id, eventmetadata_obj.get_event_fully_qal_name(),
                 payload))
    notifier_api.notify(admin_ctxt, publisher_id,
                        eventmetadata_obj.get_event_fully_qal_name(),
                        eventmetadata_obj.priority, payload)


def notify_host_update(event_type, vmHost, **kwargs):
    resource_utilization = InventoryCacheManager.get_compute_conn_driver(
        vmHost.get_id(),
        Constants.VmHost).get_resource_utilization(vmHost.get_id(),
                                                   Constants.VmHost, 5)
    # update the host event payload with utilization data and notify
    vmHost.set_utilization(resource_utilization)
    LOG.info(_('Host with (UUID, host name) - (%s, %s) got updated') %
             (vmHost.get_id(), vmHost.get_name()))
    notify(event_type, vmHost, **kwargs)
