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
A connection to a hypervisor through libvirt.

Supports KVM, LXC, QEMU, UML, and XEN.

**Related Flags**

:libvirt_type:  Libvirt domain type.  Can be kvm, qemu, uml, xen
                (default: kvm).
:libvirt_uri:  Override for the default libvirt URI (depends on libvirt_type).

"""

from healthnmon import libvirt_inventorymonitor
from healthnmon.perfmon import libvirt_perfdata
from healthnmon.virt import driver
from healthnmon import log as logging
from nova.openstack.common import cfg
import traceback

libvirt = None

LOG = logging.getLogger('healthnmon.virt.libvirt.connection')

conn_opts = [
    cfg.StrOpt('libvirt_type',
               default='kvm',
               help='Libvirt domain type (valid options are: '
                    'kvm, lxc, qemu, uml, xen)'),
    cfg.StrOpt('libvirt_uri',
               default='',
               help='Override the default libvirt URI (which is dependent'
               ' on libvirt_type)')
]
CONF = cfg.CONF
CONF.register_opts(conn_opts)


def get_connection(read_only):

    # These are loaded late so that there's no need to install these
    # libraries when not using libvirt.

    global libvirt
    if libvirt is None:
        libvirt = __import__('libvirt')

    # return LibvirtConnection._get_connection(LibvirtConnection(read_only))

    return LibvirtConnection(read_only)


class LibvirtConnection(driver.ComputeInventoryDriver):

    def __init__(self, read_only):
        super(LibvirtConnection, self).__init__()

        self._host_state = None
        self._wrapped_conn = None
        self.container = None
        self.compute_rmcontext = None
        self.uuid = None
        self.read_only = read_only
        self.libvirt_invmonitor = \
            libvirt_inventorymonitor.LibvirtInventoryMonitor()
        self.libvirt_perfmon = libvirt_perfdata.LibvirtPerfMonitor()

    def init_rmcontext(self, compute_rmcontext):
        """Initialize anything that is necessary for the driver to function"""

        self.compute_rmcontext = compute_rmcontext

    def _get_connection(self):
        if not self._wrapped_conn or not (self._wrapped_conn.isAlive() and
                                          self._test_connection()):
            LOG.debug(_('Connecting to libvirt: %s'), self.uri)
            self._wrapped_conn = self._connect(self.uri, self.read_only)
        return self._wrapped_conn

    _conn = property(_get_connection)

    def _test_connection(self):
        try:
            self._wrapped_conn.getCapabilities()
            return True
        except libvirt.libvirtError, e:
            if e.get_error_code() == libvirt.VIR_ERR_SYSTEM_ERROR \
                and e.get_error_domain() in (libvirt.VIR_FROM_REMOTE,
                                             libvirt.VIR_FROM_RPC):
                LOG.debug(_('Connection to libvirt broke'))
                return False
            raise

    @property
    def uri(self):
        if CONF.libvirt_type == 'uml':
            uri = CONF.libvirt_uri or 'uml:///system'
        elif CONF.libvirt_type == 'xen':
            uri = CONF.libvirt_uri or 'xen:///'
        elif CONF.libvirt_type == 'lxc':
            uri = CONF.libvirt_uri or 'lxc:///'
        else:
            uri = CONF.libvirt_uri or 'qemu+tls://' \
                + self.compute_rmcontext.rmIpAddress + '/system' \
                + '?no_tty=1'
        return uri

    @staticmethod
    def _connect(uri, read_only):
        auth = [[libvirt.VIR_CRED_AUTHNAME,
                libvirt.VIR_CRED_NOECHOPROMPT], 'root', None]
        conn = None
        try:
            if read_only:
                conn = libvirt.openReadOnly(uri)
            else:
                conn = libvirt.openAuth(uri, auth, 0)
        except libvirt.libvirtError:
            LOG.debug(_('Unable to connect to libvirt on the host'))
            LOG.error(_(traceback.format_exc()))
        if conn:
            conn.setKeepAlive(5, 5)
        return conn

    def get_new_connection(self, uri, read_only):
        return self._connect(uri, read_only)

    def get_libvirtError(self):
        """ Returns the refrence to Libvirt Error class """

        return libvirt.libvirtError

    libvirtError = property(get_libvirtError)

    def update_inventory(self, compute_id):
        """
        Updates the inventory details of VM Host, VMs, Network, Storage etc.,
        """
        self.libvirt_invmonitor.collectInventory(self._conn, compute_id)

    def update_perfdata(self, uuid, perfmon_type):
        """
        Refreshes the performance data of VM Host,VMs
        """

        self.libvirt_perfmon.refresh_perfdata(self._conn, uuid, perfmon_type)

    def get_resource_utilization(
        self,
        uuid,
        perfmon_type,
        window_minutes,
    ):
        """
        Returns the performance data of VM Host, VMs for specified
        window minutes. Default value of window minutes is 5 minutes """

        if self.libvirt_perfmon is not None:
            return self.libvirt_perfmon. \
                get_resource_utilization(uuid, perfmon_type, window_minutes)

    def get_inventory_monitor(self):
        if self.libvirt_invmonitor is not None:
            return self.libvirt_invmonitor

    def get_perf_monitor(self):
        if self.libvirt_perfmon is not None:
            return self.libvirt_perfmon
