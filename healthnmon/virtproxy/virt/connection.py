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

"""Abstraction of the underlying virtualization API."""

from healthnmon.virtproxy.virt import driver, fake
from healthnmon.virtproxy.virt.libvirt import connection as libvirt_conn
from nova.openstack.common import importutils
from healthnmon import log as logging
from nova import utils
import sys

LOG = logging.getLogger('healthnmon.virt.connection')


def get_connection(hypervisor_type, read_only=False):
    """
    Returns an object representing the connection to a virtualization
    platform.

    This could be :mod:`nova.virt.fake.FakeConnection` in test mode,
    a connection to KVM, QEMU, or UML via :mod:`libvirt_conn`, or a connection
    to XenServer or Xen Cloud Platform via :mod:`xenapi`.

    Any object returned here must conform to the interface documented by
    :mod:`FakeConnection`.

    **Related flags**

    :connection_type:  A string literal that falls through a if/elif structure
                       to determine what virtualization mechanism to use.
                       Values may be

                            * fake
                            * libvirt
    """

    # TODO(termie): maybe lazy load after initial check for permissions
    # TODO(termie): check whether we can be disconnected

    if hypervisor_type == 'fake':
        conn = fake.get_connection(read_only)
    elif hypervisor_type == 'QEMU':
        libvirt_conn = importutils\
            .import_module('healthnmon.virtproxy.virt.libvirt.connection')
        conn = libvirt_conn.get_connection(read_only)
    else:
        raise Exception('Unknown connection type "%s"'
                        % hypervisor_type)

    if conn is None:
        LOG.error(_('Failed to open connection to the hypervisor'))
        sys.exit(1)
    return utils.check_isinstance(conn, driver.ComputeInventoryDriver)
