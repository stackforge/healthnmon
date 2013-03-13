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

from nova.api.openstack import extensions
from ..api import storagevolume
from ..api import vmhosts
from ..api import vm
from ..api import subnet
from ..api import virtualswitch
from ..api import constants
from .. import log as logging

LOG = logging.getLogger('healthnmon.api')


class Healthnmon(extensions.ExtensionDescriptor):

    """ Health and monitoring API as nova compute extension API's
    """

    name = 'healthnmon'
    alias = 'healthnmon'
    namespace = constants.XMLNS_HEALTHNMON_EXTENSION_API
    updated = '2012-01-22T13:25:27-06:00'

    def get_resources(self):
        LOG.info(_('Adding healthnmon resource extensions'))
        resources = []
        vmhosts_resource = \
            extensions.ResourceExtension(constants.VMHOSTS_COLLECTION_NAME,
                                         vmhosts.VmHostsController(),
                                         collection_actions={'detail': 'GET'})
        vm_resource = \
            extensions.ResourceExtension(constants.VM_COLLECTION_NAME,
                                         vm.VMController(),
                                         collection_actions={'detail': 'GET'})
        storage_resource = \
            extensions.ResourceExtension(
                constants.STORAGEVOLUME_COLLECTION_NAME,
                storagevolume.StorageVolumeController(),
                collection_actions={'detail': 'GET'})
        subnet_resource = \
            extensions.ResourceExtension(constants.SUBNET_COLLECTION_NAME,
                                         subnet.SubnetController(),
                                         collection_actions={'detail': 'GET'})
        virtual_switch_resource = \
            extensions.ResourceExtension(
                constants.VIRTUAL_SWITCH_COLLECTION_NAME,
                virtualswitch.VirtualSwitchController(),
                collection_actions={'detail': 'GET'})
        resources.append(vmhosts_resource)
        resources.append(vm_resource)
        resources.append(storage_resource)
        resources.append(subnet_resource)
        resources.append(virtual_switch_resource)
        return resources
