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


import threading
import eventlet
from healthnmon import log
import healthnmon
import traceback
from healthnmon.inventory_cache_manager import InventoryCacheManager


'''Create a green pool of 200 green threads
For Processing VM which got an update'''
pool_for_processing_updated_vm = eventlet.greenpool.GreenPool(200)
LOG = log.getLogger(__name__)

libvirt = None


def start_events_thread():
    '''Called in the __init__.py of virt.libvirt package.
    It starts the thread for listening the events for the hosts registered'''
    try:
        global libvirt
        libvirt = __import__('libvirt')
        LOG.debug(_('Starting the thread for event monitoring'))
        libvirt.virEventRegisterDefaultImpl()
        t = DomainEventThread()
        t.setDaemon(True)
        t.start()
    except Exception:
        LOG.error(_('An exception occurred while starting the event thread'))
        LOG.error(_(traceback.format_exc()))


class DomainEventThread(threading.Thread):
    ''' Class to initialize the thread for event
    listening for the hosts registered'''
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            libvirt.virEventRunDefaultImpl()


class LibvirtEvents(object):

    def __init__(self):
        self.libvirt_con = None
        self.compute_id = None
        self.call_back_ids = {'domain_events': []}
        self.registered = False
        self.first_poll = True

    def register_libvirt_events(self):
        '''Initializes the libvirt connection for each host and
        calls the method to register the hosts for events.
        Currently only domain events are supported
        but the method can be extended
        for registration of events for different other resources.
        @param conn: The instance of the
            virt.libvirt.connection.LibvirtConnection class
        @param compute_id: An integer representing the
            compute id of the host'''
        try:
            self.call_back_ids['domain_events'][:] = []
            conn_driver = InventoryCacheManager.get_compute_inventory(
                self.compute_id).get_compute_conn_driver()
            self.libvirt_con = conn_driver.get_new_connection(
                conn_driver.uri, True)
            if self.libvirt_con is None:
                self.first_poll = True
                return
            self._register_libvirt_domain_events()
            self.registered = True
        except Exception:
            self.first_poll = True
            self.deregister_libvirt_events()
            LOG.error(_('An exception occurred while \
            registering the host for events'))
            LOG.error(_(traceback.format_exc()))

    def _register_libvirt_domain_events(self):
        '''Register the hosts for domain events
        Stores the callback ids for the each event for hosts in the list
        The call back ids are mainly used for deregistering
        the hosts for the events'''
        LOG.debug(_('Registering host with compute id %s for events' %
                  str(self.compute_id)))
        self.call_back_ids['domain_events'].append(
            self.libvirt_con.domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                self._domain_event_callback, None))
        self.call_back_ids['domain_events'].append(
            self.libvirt_con.domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_REBOOT,
                self._domain_event_callback, None))

    def deregister_libvirt_events(self):
        '''De-registers the hosts for libvirt events '''
        try:
            if self.registered:
                self.registered = False
                self._deregister_libvirt_domain_events()
        except Exception:
            LOG.error(_('An exception occurred while \
            deregistering the host for events'))
            LOG.error(_(traceback.format_exc()))
        finally:
            self.call_back_ids['domain_events'][:] = []
            if self.libvirt_con is not None:
                self.libvirt_con.close()
                self.libvirt_con = None

    def _deregister_libvirt_domain_events(self):
        '''Deregisters the hosts for domain events by calling
        the domainEventDeregisterAny method
        of the libvirt. It uses the domain events' callback ids
        for the deregistration of the hosts'''
        LOG.debug(_('Deregistering the host with compute id %s for events' %
                  str(self.compute_id)))
        for callBackId in self.call_back_ids['domain_events']:
            self.libvirt_con.domainEventDeregisterAny(callBackId)

    def _process_updates_for_updated_domain(self, domainObj):
        '''Calls the processUpdatesForDomainUpdated method of the LibvirtVM
        which processes the VM for the updates which was reported by the
        libvirt domain event.
        @param domainobj: An object of the class virDomain of libvirt
        This object holds the VM parameters needs to processed'''
        libvirtVmobj = healthnmon.libvirt_inventorymonitor.LibvirtVM(
            self.libvirt_con, self.compute_id)
        libvirtVmobj.process_updates_for_updated_VM(domainObj)

    def _domain_event_callback(self, *args):
        '''The method is callback registered fot the domain events
        @param args: A tuple passed implicitly by the method
        domainEventRegisterAny by libvirt.
        The length and the content varies depending upon
        the event calling this callback
        The first two values are the libvirt connection and
        the virDomain's domainobj necessarily.'''
        try:
            pool_for_processing_updated_vm.spawn_n(
                self._process_updates_for_updated_domain, args[1])
            pool_for_processing_updated_vm.waitall()
        except Exception:
            LOG.error(_('An exception occurred in the domain event callback'))
            LOG.error(_(traceback.format_exc()))
