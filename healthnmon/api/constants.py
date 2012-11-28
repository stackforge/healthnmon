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

''' Constants for api module '''

XMLNS_HEALTHNMON_EXTENSION_API = \
    'http://docs.openstack.org/ext/healthnmon/api/v2.0'
XMLNS_ATOM = 'http://www.w3.org/2005/Atom'
ATOM = '{%s}' % XMLNS_ATOM

STORAGEVOLUME_COLLECTION_NAME = 'storagevolumes'
VMHOSTS_COLLECTION_NAME = 'vmhosts'
VM_COLLECTION_NAME = 'virtualmachines'
SUBNET_COLLECTION_NAME = 'subnets'
VIRTUAL_SWITCH_COLLECTION_NAME = 'virtualswitches'

MEMBER_MAP = {
    'vmhost': VMHOSTS_COLLECTION_NAME,
    'virtualmachine': VM_COLLECTION_NAME,
    'subnet': SUBNET_COLLECTION_NAME,
    'virtualswitch': VIRTUAL_SWITCH_COLLECTION_NAME,
    'storagevolume': STORAGEVOLUME_COLLECTION_NAME,
}

QUERY_FIELD_KEY = 'fields'
PERFORMANCE_DATA_ATTRIBUTES = (
    'cpuUserLoad',
    'cpuSystemLoad',
    'hostCpuSpeed',
    'hostMaxCpuSpeed',
    'ncpus',
    'diskRead',
    'diskWrite',
    'netRead',
    'netWrite',
    'totalMemory',
    'freeMemory',
    'configuredMemory',
    'uptimeMinute',
    'reservedSystemCapacity',
    'maximumSystemCapacity',
    'relativeWeight',
    'reservedSystemMemory',
    'maximumSystemMemory',
    'memoryRelativeWeight',
    'uuid',
)
