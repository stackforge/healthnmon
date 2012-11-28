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

from sqlalchemy import Column, Integer, String, MetaData, ForeignKey, \
    Boolean, Numeric, Enum, BigInteger
from sqlalchemy.schema import Table
from healthnmon import log as logging


LOG = logging.getLogger('healthnmon.db.models')
meta = MetaData()


def __common_columns():
    """
        List of common column definitions for entity sub classes.
    """
    return (Column('createEpoch', BigInteger),
            Column('lastModifiedEpoch', BigInteger),
            Column('deletedEpoch', BigInteger),
            Column('deleted', Boolean, default=False))


Cost = Table('healthnmon_cost', meta, Column('id', Integer,
             primary_key=True, autoincrement=True), Column('value',
             Numeric(16, 2)), Column('units', String(255)))

OsProfile = Table(
    'healthnmon_os_profile',
    meta,
    Column('resourceId', String(255), primary_key=True, unique=True),
    Column('osType', Enum(
        'WINDOWS',
        'WINDOWS_2008',
        'WINDOWS_LH',
        'LINUX',
        'HP_UX',
        'VMWARE',
        'HYPER_V',
        'KVM',
        'CITRIX_XEN',
        'SOLARIS',
        'AIX',
        'OPEN_VMS',
        'UNKNOWN',
        'UNSPECIFIED',
        name='OsTypeEnum_PServer',
    )),
    Column('osSubType', String(255)),
    Column('osDescription', String(255)),
    Column('osName', String(255)),
    Column('osVersion', String(255)),
)

PhysicalServer = Table(
    'healthnmon_physical_server',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer(), ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('memorySize', BigInteger),
    Column('processorSpeedMhz', Integer),
    Column('processorSpeedTotalMhz', Integer),
    Column('processorCount', Integer),
    Column('processorCoresCount', Integer),
    Column('processorArchitecture', Enum(
        'IA_32',
        'IA_64',
        'X86_64',
        'SPARC',
        'POWER_PC',
        'UNSPECIFIED',
        name='ProcessorArchitectureEnum',
    )),
    Column('hyperThreadEnabled', Boolean),
    Column('serialNumber', String(255)),
    Column('groupId', String(255)),
    Column('memoryConsumed', BigInteger),
    Column('processorLoadPercent', Integer),
    Column(
        'osId', String(255), ForeignKey('healthnmon_os_profile.resourceId')),
    Column('model', String(255)),
    Column('licensingId', String(255)),
    Column('enclosure', String(255)),
    Column('bay', String(255)),
    Column('uuid', String(255)),
    Column('inUse', Boolean),
    Column('fcVirtualInitiator', Boolean),
    Column('ethernetVirtualInitiator', Boolean),
    Column('validTarget', Boolean),
    *(__common_columns())
)

ResourceUtilization = Table(
    'healthnmon_resource_utilization',
    meta,
    Column('resourceId', String(255),
           ForeignKey('healthnmon_physical_server.id',
           ondelete='CASCADE'), primary_key=True),
    Column('memorySize', BigInteger),
    Column('memoryConsumed', BigInteger),
    Column('diskSpace', BigInteger),
    Column('diskSpaceConsumed', BigInteger),
    Column('cpuPercentUsed', BigInteger),
    Column('networkPercentUsed', BigInteger),
)

ResourceLimit = Table(
    'healthnmon_resource_limit',
    meta,
    Column('resourceId', String(255),
           ForeignKey('healthnmon_physical_server.id',
           ondelete='CASCADE'), primary_key=True),
    Column('memoryConsumedLimit', BigInteger),
    Column('memoryPercentLimit', BigInteger),
    Column('diskSpaceConsumedLimit', BigInteger),
    Column('diskSpacePercentLimit', BigInteger),
    Column('cpuPercentLimit', BigInteger),
    Column('networkPercentLimit', BigInteger),
)

VmHost = Table(
    'healthnmon_vm_host',
    meta,
    Column('id', String(255), ForeignKey('healthnmon_physical_server.id',
                                         ondelete='CASCADE'), primary_key=True),
    Column('resourceManagerId', String(255)),
    Column('virtualizationType', Enum(
        'ESX',
        'XEN',
        'HYPER_V',
        'MSVS',
        'GSX',
        'INTEGRITY_VM',
        'CLOUD',
        'KVM',
        'QEMU',
        'UNKNOWN',
        name='VirtualizationEnum',
    )),
    Column('clusterName', String(255)),
    Column('ftEnabled', Boolean),
    Column('liveMoveEnabled', Boolean),
    Column('storageMoveEnabled', Boolean),
    Column('sharedDisksEnabled', Boolean),
    Column('linkedCloneEnabled', Boolean),
    Column('connectionState', String(255)),
    Column('isMaintenanceMode', Boolean),
    Column('powerState', String(255)),
    *(__common_columns())
)

IpProfile = Table(
    'healthnmon_ip_profile',
    meta,
    Column('ipAddress', String(255), primary_key=True),
    Column('ipType', Enum('IPV4', 'IPV6', 'UNSPECIFIED',
           name='IpTypeEnum')),
    Column('hostname', String(255), primary_key=True),
    Column('domain', String(255)),
    Column('vmHostId', String(255), ForeignKey('healthnmon_vm_host.id'
                                               )),
    Column('vmId', String(255), ForeignKey('healthnmon_vm.id')),
)

VirtualSwitch = Table(
    'healthnmon_virtual_switch',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer(), ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('switchType', String(255)),
    Column('subnetIds', String(255)),
    Column('networkInterfaces', String(255)),
    Column('connectionState', String(255)),
    Column('vmHostId', String(255), ForeignKey('healthnmon_vm_host.id')),
    *(__common_columns())
)

PortGroup = Table(
    'healthnmon_port_group',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer(), ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('type', String(255)),
    Column('virtualSwitchId', String(255),
           ForeignKey('healthnmon_virtual_switch.id')),
    Column('vmHostId', String(255), ForeignKey('healthnmon_vm_host.id')),
    *(__common_columns())
)

StorageVolume = Table(
    'healthnmon_storage_volume',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('value', Numeric(16, 2)),
    Column('units', String(255)),
    Column('resourceManagerId', String(255)),
    Column('size', BigInteger),
    Column('free', BigInteger),
    Column('vmfsVolume', Boolean),
    Column('shared', Boolean),
    Column('assignedServerCount', Integer),
    Column('volumeType', Enum(
        'FC_SAN',
        'DAS',
        'VMFS',
        'SAS_SAN',
        'ISCSI_SAN',
        'DIR',
        'FS',
        'DISK',
        'NETFS',
        'ISCSI',
        'SCSI',
        'LOGICAL',
        'MPATH',
        'UNSPECIFIED',
        name='StorageTypeEnum',
    )),
    Column('volumeId', String(255)),
    Column('connectionState', String(255)),
    Column('physicalServerId', String(255),
           ForeignKey('healthnmon_physical_server.id')),
    *(__common_columns())
)

HostMountPoint = Table(
    'healthnmon_host_mount_point',
    meta,
    Column('path', String(255)),
    Column('vmHostId', String(255),
           ForeignKey(
           'healthnmon_vm_host.id', ondelete='CASCADE'), primary_key=True),
    Column('storageVolumeId', String(255),
           ForeignKey(
           'healthnmon_storage_volume.id', ondelete='CASCADE'), primary_key=True),
)

ResourceAllocation = Table(
    'healthnmon_resource_allocation',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('share', Enum('LOW', 'NORMAL', 'HIGH', 'CUSTOM',
           name='ResourceAllocationShareEnum')),
    Column('customShareValue', Integer),
    Column('reservation', BigInteger),
    Column('isExpandableReservation', Boolean),
    Column('limit', BigInteger),
    Column('isUnlimited', Boolean),
)

VmCapacityPool = Table(
    #    Although extended from ResourceCapacityPool, it is made to extend from Resource table
    #    as there is no additional attribute in ResourceCapacityPool. Need to handle in Mapper level
    #     ForeignKey to VmCluster.entityId or VmHost.entityId . Currently it is kept as is without FK
    #    capacityPools:  Many to One relationship with VmHost table
    'healthnmon_vm_capacity_pool',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('value', Numeric(16, 2)),
    Column('units', String(255)),
    Column('resourceManagerId', String(255)),
    Column('virtualizationType', Enum(
        'ESX',
        'XEN',
        'HYPER_V',
        'MSVS',
        'GSX',
        'INTEGRITY_VM',
        'CLOUD',
        'KVM',
        'QEMU',
        'UNKNOWN',
        name='VirtualizationEnum_Cap',
    )),
    Column('parentId', String(255)),
    Column('parentName', String(255)),
    Column('cpuResourceAllocationId', Integer,
           ForeignKey('healthnmon_resource_allocation.id')),
    Column('memoryResourceAllocationId', Integer,
           ForeignKey('healthnmon_resource_allocation.id')),
    Column('diskResourceAllocationId', Integer,
           ForeignKey('healthnmon_resource_allocation.id')),
    Column('vmHostId', String(255), ForeignKey('healthnmon_vm_host.id'
                                               )),
    *(__common_columns())
)

#    capacityPools:  Many to One relationship with VmCluster table
LoadBalancer = Table(
    #   subnetIds: One-to-Many relationship with SubNet
    #    TODO: Needs a relation one-to-many with whom :ResourceTag
    'healthnmon_load_balancer',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('resourceManagerId', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('model', String(255), nullable=False),
    Column('version', String(255), nullable=False),
    Column('managementAddress', String(255), nullable=False),
    Column('managementPort', Integer, nullable=False),
    Column('managementUserName', String(255)),
    Column('managementPasswordId', String(255)),
    Column('managementCertificateId', String(255)),
    Column('isHaSupported', Enum('YES', 'NO', 'UNSPECIFIED',
           name='YesNoTriple')),
    Column('isHaSupported', Enum('YES', 'NO', 'UNSPECIFIED',
           name='YesNoTriple')),
    Column('tags', String(255)),
    *(__common_columns())
)

Subnet = Table(
    'healthnmon_subnet',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('description', String(255)),
    Column('networkAddress', String(255)),
    Column('networkMask', String(255)),
    Column('networkSources', String(255)),
    Column('ipType', Enum('IPV4', 'IPV6', 'UNSPECIFIED',
           name='IpTypeEnum_Subnet')),
    Column('isPublic', Boolean),
    Column('isShareable', Boolean),
    Column('dnsDomain', String(255)),
    Column('dnsServers', String(255)),
    Column('dnsSearchSuffixes', String(255)),
    Column('defaultGateways', String(255)),
    Column('msDomainType', Enum('WORKGROUP', 'DOMAIN',
           name='MsDomainTypeEnum')),
    Column('msDomainName', String(255)),
    Column('winsServers', String(255)),
    Column('ntpDateServers', String(255)),
    Column('vlanId', String(255)),
    Column('isBootNetwork', Boolean),
    Column('deploymentServices', String(255)),
    Column('parentIds', String(255)),
    Column('childIds', String(255)),
    Column('isTrunk', Boolean),
    Column('redundancyPeerIds', String(255)),
    Column('redundancyMasterId', String(255)),
    Column('isNativeVlan', Boolean),
    Column('loadBalancerId', String(255),
           ForeignKey('healthnmon_load_balancer.id')),
    *(__common_columns())
)

GroupIdType = Table('healthnmon_groupid_type', meta,
                    Column('id', String(255), primary_key=True),
                    Column('networkTypes', String(255)),
                    Column('subnetId', String(255),
                           ForeignKey('healthnmon_subnet.id')),
                    )

ResourceTag = Table(
    'healthnmon_resource_tag',
    meta,
    Column('id', Integer, autoincrement=True, primary_key=True),
    Column('value', String(255), nullable=False),
    Column('assertionType', String(255), nullable=False),
    Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id',
           ondelete='CASCADE')),
)

#  ============== Vm Tables Start ==================

VmGlobalSettings = Table(
    #    vmGlobalSettings: One-to-One relation handled in Vm table
    'healthnmon_vm_global_settings',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer(), ForeignKey('healthnmon_cost.id')),
    Column('autoStartAction', String(255)),
    Column('autoStopAction', String(255)),
    *(__common_columns())
)


Vm = Table(
    #    os : One-to-One relation with OsProfile
    #   ipAddresses: One-to-Many Relation handled in IpProfile table
    #   VmNetAdapters: One-to-Many Relation handled in VmNetAdapter table
    #   VmScsiControllers: One-to-Many Relation handled in VmScsiController table
    #   VmDisks: One-to-Many Relation handled in VmDisk table
    #   VmGenericDevice: One-to-Many Relation handled in VmGenericDevice table
    #   vmGlobalSettings: One-to-One Relation with vmGlobalSettings
    #    Column('autoStartAction',String(255)),
    #    Column('autoStopAction',String(255)),
    #   capabilities : One-to-One Relation with VmCapabilities
    #    Column('templateId', String(255), ForeignKey('healthnmon_vm_template.id')), TBD
    #   vmHostId: One-to-many Relation with VmHost
    #   One-to-One Relation with ResourceAllocation
    #   One-to-One Relation with ResourceAllocation
    #   vmClusterId: One-to-many Relation with vmCluster
    #    Column('vmClusterId', String(255), ForeignKey('healthnmon_vm_cluster.id')),TBD
    #   vmCapacityPoolId: One-to-many Relation with vmCapacityPool
    'healthnmon_vm',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer(), ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('memorySize', BigInteger),
    Column('processorSpeedMhz', Integer),
    Column('processorSpeedTotalMhz', Integer),
    Column('processorCount', Integer),
    Column('processorCoresCount', Integer),
    Column('processorArchitecture', Enum(
        'IA_32',
        'IA_64',
        'X86_64',
        'SPARC',
        'POWER_PC',
        'UNSPECIFIED',
        name='ProcessorArchitectureEnum_vm',
    )),
    Column('serialNumber', String(255)),
    Column('groupId', String(255)),
    Column('memoryConsumed', BigInteger),
    Column('processorLoadPercent', Integer),
    Column('virtualizationType', Enum(
        'ESX',
        'XEN',
        'HYPER_V',
        'MSVS',
        'GSX',
        'INTEGRITY_VM',
        'CLOUD',
        'KVM',
        'QEMU',
        'UNKNOWN',
        name='VirtualizationEnum_Vm',
    )),
    Column(
        'osId', String(255), ForeignKey('healthnmon_os_profile.resourceId')),
    Column('powerState', String(255)),
    Column('connectionState', String(255)),
    Column('bootOrder', String(255)),
    Column('globalSettingsId', String(255),
           ForeignKey('healthnmon_vm_global_settings.id')),
    Column('haEnabled', Boolean),
    Column('ftEnabled', Boolean),
    Column('liveMoveEnabled', Boolean),
    Column('storageMoveEnabled', Boolean),
    Column('sharedDisksEnabled', Boolean),
    Column('linkedCloneEnabled', Boolean),
    Column('vmHostId', String(255), ForeignKey('healthnmon_vm_host.id'
                                               )),
    Column('cpuResourceAllocationId', BigInteger,
           ForeignKey('healthnmon_resource_allocation.id')),
    Column('memoryResourceAllocationId', BigInteger,
           ForeignKey('healthnmon_resource_allocation.id')),
    Column('vmCapacityPoolId', String(255),
           ForeignKey('healthnmon_vm_capacity_pool.id')),
    *(__common_columns())
)

VmNetAdapter = Table(
    #    One-to-Many relationship with IPAddress TODO
    #    Verify: IpProfile / IpAddress ? Rework: IPAddress ? Will it be a list?
    #    netAdapters: Many-to-One relation with netAdapter table
    'healthnmon_vm_net_adapter',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('value', Numeric(16, 2)),
    Column('units', String(255)),
    Column('addressType', String(255)),
    Column('adapterType', String(255)),
    Column('switchType', String(255)),
    Column('macAddress', String(255)),
    Column('ipAddresses', String(255)),
    Column('networkName', String(255)),
    Column('vlanId', String(255)),
    Column('vmId', String(255), ForeignKey('healthnmon_vm.id',
           ondelete='CASCADE')),
)

VmScsiController = Table(
    #    vmScsiControllers: Many-to-One relation with Vm
    'healthnmon_vm_scsi_controller',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('value', Numeric(16, 2)),
    Column('units', String(255)),
    Column('controllerId', Integer),
    Column('controllerName', String(255)),
    Column('type', String(255)),
    Column('busSharing', String(255)),
    Column('vmId', String(255), ForeignKey('healthnmon_vm.id',
           ondelete='CASCADE')),
)

VmDisk = Table(
    # CHANGE to list TBD
    # CHANGE to list  TBD
    #    storageVolumeId: Foreginkey to storageVolume.entityId or sanvolume.entityId
    #    Need to handle in Mapper appropriately
    'healthnmon_vm_disk',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('value', Numeric(16, 2)),
    Column('units', String(255)),
    Column('controllerType', String(255)),
    Column('controllerId', Integer),
    Column('channel', Integer),
    Column('fileName', String(255)),
    Column('mode', String(255)),
    Column('diskSize', BigInteger),
    Column('fileSize', BigInteger),
    Column('lunId', String(255)),
    Column('deviceDescription', String(255)),
    Column('hostHbaNodeWwn', String(255)),
    Column('hostHbaPortWwn', String(255)),
    Column('npivNodeWwns', String(255)),
    Column('npivPortWwns', String(255)),
    Column('compatibilityMode', String(255)),
    Column('storageVolumeId', String(255),
           ForeignKey('healthnmon_storage_volume.id')),
    Column('vmId', String(255), ForeignKey('healthnmon_vm.id',
           ondelete='CASCADE')),
)

VmGenericDevice = Table('healthnmon_vm_generic_device', meta,
                        Column('id', String(255), primary_key=True),
                        Column('name', String(255)),
                        Column('vmId', String(255), ForeignKey('healthnmon_vm.id', ondelete='CASCADE')))

VmProperty = Table(
    'healthnmon_vm_property',
    meta,
    Column('id', Integer, autoincrement=True, primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('value', String(255)),
    Column('vmDeviceId', String(255),
           ForeignKey('healthnmon_vm_generic_device.id',
           ondelete='CASCADE')),
)

# ========== Vm Tables End ===================

# ========== Cluster Tables End ===================

ComputeCluster = Table(
    'healthnmon_compute_cluster',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('processorSpeedTotalMhz', Integer),
    Column('memorySize', BigInteger),
    Column('processorCoresCount', Integer),
    Column('hostsCount', Integer),
    Column('effectiveHostsCount', Integer),
    Column('effectiveProcessorSpeedTotalMhz', Integer),
    Column('effectiveMemorySize', BigInteger),
    Column('memoryConsumed', BigInteger),
    Column('processorLoadPercent', Integer),
    *(__common_columns())
)

#    computeServers:    One-to-Many relationship handled in ComputeServer

VmCluster = Table(
    'healthnmon_vm_cluster',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('virtualizationType', Enum(
        'ESX',
        'XEN',
        'HYPER_V',
        'MSVS',
        'GSX',
        'INTEGRITY_VM',
        'CLOUD',
        'KVM',
        'QEMU',
        'UNKNOWN',
        name='VirtualizationEnum_cluster',
    )),
    Column('haEnabled', Boolean),
    Column('drsEnabled', Boolean),
    Column('dpmEnabled', Boolean),
    Column('computeClusterId', String(255),
           ForeignKey('healthnmon_compute_cluster.id',
           ondelete='CASCADE')),
    *(__common_columns())
)

#    hosts:    One-to-many relationship handled in VmHost

#    TODO: One-to-many : Will volumeId of StorageValome have any relation with this ?

#    Verify: Handle relationship with VirtualSwitches
#    Verify: Handle relationship with PortGroup
#    TODO: Handle relationship with VmCapacityPool in mapper level
#    VirtualMachineIds: One-to-many relationship handled in  Vm

IpAddressRange = Table(
    #    ipAddressRanges:    Many-to-one relationship with Subnet table
    'healthnmon_ip_address_range',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('startAddressId', String(255),
           ForeignKey('healthnmon_ip_address.id')),
    Column('endAddressId', String(255),
           ForeignKey('healthnmon_ip_address.id')),
    Column('allocationType', Enum('DHCP', 'AUTO_STATIC',
           name='IpAllocationTypeEnum_range')),
    Column('addressRangeCount', Integer),
    Column('usedIpAddressCount', Integer),
    Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id'),
           primary_key=True),
    *(__common_columns())
)

IpAddress = Table(
    #    usedIpAddresses:    Many-to-one relationship with Subnet

    'healthnmon_ip_address',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('rangeId', String(255)),
    Column('address', String(255)),
    Column('allocationType', Enum('DHCP', 'AUTO_STATIC',
           name='IpAllocationTypeEnum')),
    Column('inMaintenance', Boolean, default=False),
    Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id'
                                               )),
    *(__common_columns())
)

# ========== Cluster Tables End ===================
# ========== VmTemplate Tables Start ===================

DeployableSoftware = Table(
    #   os:  One to one relationship with OsProfile
    'healthnmon_deployable_software',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column(
        'osId', String(255), ForeignKey('healthnmon_os_profile.resourceId')),
    Column('location', String(255)),
    Column('size', BigInteger),
    Column('memorySize', BigInteger),
    Column('processorCount', Integer),
    Column('processorArchitecture', Enum(
        'IA_32',
        'IA_64',
        'X86_64',
        'SPARC',
        'POWER_PC',
        'UNSPECIFIED',
        name='ProcessorArchitectureEnum_DS',
    )),
    *(__common_columns())
)

CloudImage = Table('healthnmon_cloud_image', meta, Column('id',
                   String(255),
                   ForeignKey('healthnmon_deployable_software.id',
                   ondelete='CASCADE'), primary_key=True),
                   Column('sourceCapacityPoolIds', String(255)))  # Verify : Probably needs relationship

Image = Table('healthnmon_image', meta, Column('id', String(255),
              ForeignKey('healthnmon_deployable_software.id',
              ondelete='CASCADE'), primary_key=True), Column('type',
              Enum('OS', 'APPS', 'PATCH', name='ImageTypeEnum')),
              Column('dsType', Enum('RDP', 'SA', 'IGNITE_UX', 'CUSTOM',
              name='DeploymentServiceTypeEnum')))

VmTemplate = Table(
                    #    vmNetAdapters: One-to-Many relation with vmNetAdapter
                     #    vmScsiControllers: One-to-Many relation with vmScsiController
                     #    vmDisks: One-to-Many relation with vmDisk
                     #    vmGenericDevices: One-to-Many relation with VmGenericDevice
                     #    vmGlobalSettings: One-to-Many relation with VmGlobalSetting
                     #    vmDisks: One-to-Many relation with vmDisk
    'healthnmon_vm_template',
    meta,
    Column('id', String(255),
           ForeignKey('healthnmon_deployable_software.id',
           ondelete='CASCADE'), primary_key=True),
    Column('virtualizationType', Enum(
        'ESX',
        'XEN',
        'HYPER_V',
        'MSVS',
        'GSX',
        'INTEGRITY_VM',
        'CLOUD',
        'KVM',
        'QEMU',
        'UNKNOWN',
        name='VirtualizationEnum_template',
        )),
    Column('autoStartAction', String(255)),
    Column('autoStopAction', String(255)),
    Column('vmHostId', String(255), ForeignKey('healthnmon_vm_host.id'
           )),
    Column('cpuResourceAllocation', Integer,
           ForeignKey('healthnmon_resource_allocation.id')),
    Column('memoryResourceAllocation', Integer,
           ForeignKey('healthnmon_resource_allocation.id')),
    )

# ========== VmTemplate Tables End ===================
# ========== SAN Volume Tables Start ===================

SanVolumeTemplate = Table(
                        # tags: One-to-Many relation handled in ResourceTags
                        # TODO : A list
                        # TODO : A list
    'healthnmon_san_volume_template',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('spmId', String(255)),
    Column('description', String(255)),
    Column('storageTemplateType', Enum('UNKNOWN', 'SPM', 'SPMDEFAULT',
           'LSMDEFAULT', name='StorageTemplateTypeEnum')),
    Column('spmTemplateId', String(255)),
    Column('provisioningType', Enum('THICK', 'THIN', 'UNKNOWN',
           name='StorageProvisioningTypeEnum')),
    Column('size', BigInteger),
    Column('raidLevel', Enum(
        'RAID0',
        'RAID1',
        'RAID3',
        'RAID4',
        'RAID5',
        'RAID6',
        'RAID01',
        'RAID05',
        'RAID10',
        'RAID50',
        'RAID60',
        'AUTO',
        'UNSPECIFIED',
        name='RaidLevelEnum',
        )),
    Column('osType', Enum(
        'WINDOWS',
        'WINDOWS_2008',
        'WINDOWS_LH',
        'LINUX',
        'HP_UX',
        'VMWARE',
        'HYPER_V',
        'KVM',
        'CITRIX_XEN',
        'SOLARIS',
        'AIX',
        'OPEN_VMS',
        'UNKNOWN',
        'UNSPECIFIED',
        name='OsTypeEnum_San_Vm',
        )),
    Column('minSize', BigInteger),
    Column('maxSize', BigInteger),
    Column('allowedRaidLevels', Enum(
        'RAID0',
        'RAID1',
        'RAID3',
        'RAID4',
        'RAID5',
        'RAID6',
        'RAID01',
        'RAID05',
        'RAID10',
        'RAID50',
        'RAID60',
        'AUTO',
        'UNSPECIFIED',
        name='RaidLevelEnum_Sec',
        )),
    Column('allowedOsTypes', Enum(
        'WINDOWS',
        'WINDOWS_2008',
        'WINDOWS_LH',
        'LINUX',
        'HP_UX',
        'VMWARE',
        'HYPER_V',
        'KVM',
        'CITRIX_XEN',
        'SOLARIS',
        'AIX',
        'OPEN_VMS',
        'UNKNOWN',
        'UNSPECIFIED',
        name='OsTypeEnum_San_Vm_Sec',
        )),
    Column('requiredTags', String(255)),
    Column('excludeTags', String(255)),
    *(__common_columns())
    )

WwnConnection = Table(  # Verify: Do you need this id?
                        # Verify: Does it have foreign key to itself ?
    'healthnmon_wwn_connection',
    meta,
    Column('id', Integer, autoincrement=True, primary_key=True),
    Column('serverWwn', String(255)),
    Column('targetWwns', String(255)),
    Column('fabricId', String(255)),
    Column('presentation', String(255)),
    )

ExtensibleRaidLevel = Table('healthnmon_extensible_raid_level', meta,
                            Column('id', Integer, autoincrement=True,
                            primary_key=True), Column('raidLevelEnum',
                            Enum(
    'RAID0',
    'RAID1',
    'RAID3',
    'RAID4',
    'RAID5',
    'RAID6',
    'RAID01',
    'RAID05',
    'RAID10',
    'RAID50',
    'RAID60',
    'AUTO',
    'UNSPECIFIED',
    name='RaidLevelEnum_third',
    )), Column('extendedRaidLevel', String(255)))

DiskArray = Table(
    'healthnmon_disk_array',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    *(__common_columns())
    )

#    sanVolumes: One-to-many relation handled in SanVolume

SanVolume = Table(  # TODO Relation with ResourceTag
    'healthnmon_san_volume',
    meta,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('note', String(255)),
    Column('costId', Integer, ForeignKey('healthnmon_cost.id')),
    Column('resourceManagerId', String(255)),
    Column('size', BigInteger),
    Column('extensibleRaidLevel',
           ForeignKey('healthnmon_extensible_raid_level.id')),
    Column('osType', Enum(
        'WINDOWS',
        'WINDOWS_2008',
        'WINDOWS_LH',
        'LINUX',
        'HP_UX',
        'VMWARE',
        'HYPER_V',
        'KVM',
        'CITRIX_XEN',
        'SOLARIS',
        'AIX',
        'OPEN_VMS',
        'UNKNOWN',
        'UNSPECIFIED',
        name='OsTypeEnum_San',
        )),
    Column('diskArrayId', ForeignKey('healthnmon_disk_array.id')),
    Column('lunId', String(255)),
    Column('tags', String(255)),
    Column('groupId', String(255)),
    Column('setId', String(255)),
    Column('isMultiMemberSet', Boolean),
    Column('setName', String(255)),
    Column('availableConnectionCount', Integer),
    Column('isBootable', Boolean),
    Column('inUse', Boolean),
    Column('isSinglePath', Boolean),
    Column('volumeState', Enum('LSM', 'SPM_PRE_CARVED',
           'SPM_NOT_CARVED', 'UNKNOWN', name='VolumeStateEnum')),
    Column('provisioningType', Enum('THICK', 'THIN', 'UNKNOWN',
           name='StorageProvisioningTypeEnum_Second')),
    Column('wwnConnections', Integer,
           ForeignKey('healthnmon_wwn_connection.id')),
    Column('isAutoGenerated', Boolean),
    Column('isManualZoningRequired', Boolean),
    *(__common_columns())
    )

# ========== SAN Volume Tables Ednd ===================
# ========== List Tables Start ===================

VirtualSwitchSubnetIds = Table('healthnmon_virtual_switch_subnet_ids', meta,
                       Column('subnetId', String(255),
                                      ForeignKey(
                                          'healthnmon_subnet.id'), primary_key=True),
                       Column('virtualSwitchId', String(255),
                                      ForeignKey('healthnmon_virtual_switch.id'), primary_key=True))

NetworkInterfaces = Table('healthnmon_network_interfaces', meta,
                       Column('interfaceId', String(255), primary_key=True),
                       Column('vSwitchId', String(255),
                                 ForeignKey('healthnmon_virtual_switch.id'), primary_key=True))

SubnetNetworkSources = Table('healthnmon_subnet_network_sources', meta,
                       Column(
                           'networkSourceId', String(255), primary_key=True),
                       Column('subnetId', String(255),
                                ForeignKey('healthnmon_subnet.id'), primary_key=True))

SubnetDnsServers = Table('healthnmon_subnet_dns_servers', meta,
                       Column('dnsServerId', String(255), primary_key=True),
                       Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id')))

SubnetDnsSearchSuffixes = Table('healthnmon_subnet_dns_search_suffixes', meta,
                       Column('dnsSuffixId', String(255), primary_key=True),
                       Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id')))

SubnetDefaultGateways = Table('healthnmon_subnet_default_gateways', meta,
                      Column(
                          'defaultGatewayId', String(255), primary_key=True),
                      Column(
                          'subnetId', String(
                              255), ForeignKey('healthnmon_subnet.id'),
                             primary_key=True))

SubnetWinServers = Table('healthnmon_subnet_win_servers', meta,
                       Column('winServerId', String(255), primary_key=True),
                       Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id')))

SubnetNtpDateServers = Table('healthnmon_subnet_ntp_date_servers', meta,
                       Column(
                           'ntpDateServerId', String(255), primary_key=True),
                       Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id')))

SubnetDeploymentServices = Table('healthnmon_subnet_deployment_services', meta,
                       Column('deploymentServiceId',
                              String(255), primary_key=True),
                       Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id')))

GroupIdTypeNetworkTypes = Table('healthnmon_groupid_type_network_type', meta,
                       Column('id', Integer,
                              autoincrement=True, primary_key=True),
                       Column('networkTypeId', String(255)),
                       Column('groupTypeId', String(255),
                               ForeignKey('healthnmon_groupid_type.id')))

SubnetParentIds = Table('healthnmon_subnet_parent_ids', meta,
                       Column('parentId', String(255), primary_key=True),
                       Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id')))

SubnetChildIds = Table('healthnmon_subnet_child_ids', meta,
                       Column('childId', String(255), primary_key=True),
                       Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id')))

SubnetRedundancyPeerIds = Table('healthnmon_subnet_redundancy_peer_ids', meta,
                       Column(
                           'redundancyPeerId', String(255), primary_key=True),
                       Column('subnetId', String(255), ForeignKey('healthnmon_subnet.id')))

VmNetAdapterIpProfiles = Table('healthnmon_vm_netadapter_ip_address', meta,
                       Column('ipAddress', String(255), primary_key=True),
                       Column('netAdapterId', String(255),
                              ForeignKey('healthnmon_vm_net_adapter.id'), primary_key=True))

# ========== List Tables Start ===================

up_tables = [
    Cost,
    OsProfile,
    PhysicalServer,
    ResourceUtilization,
    ResourceLimit,
    VmHost,
    VirtualSwitch,
    PortGroup,
    NetworkInterfaces,
    StorageVolume,
    HostMountPoint,
    ResourceAllocation,
    VmCapacityPool,
    VmGlobalSettings,
    Vm,
    IpProfile,
    VmNetAdapter,
    VmScsiController,
    VmDisk,
    VmNetAdapterIpProfiles,
    VmGenericDevice,
    VmProperty,
    LoadBalancer,
    Subnet,
    GroupIdType,
    ResourceTag,
    ComputeCluster,
    VmCluster,
    DeployableSoftware,
    CloudImage,
    Image,
    VmTemplate,
    SanVolumeTemplate,
    WwnConnection,
    ExtensibleRaidLevel,
    DiskArray,
    SanVolume,
    VirtualSwitchSubnetIds,
    SubnetNetworkSources,
    SubnetDnsServers,
    SubnetDnsSearchSuffixes,
    SubnetDefaultGateways,
    SubnetWinServers,
    SubnetNtpDateServers,
    SubnetDeploymentServices,
    SubnetParentIds,
    SubnetChildIds,
    SubnetRedundancyPeerIds,
    GroupIdTypeNetworkTypes,
    IpAddress,
    IpAddressRange
    ]


def upgrade(migrate_engine):
    """
     Upgrade operations go here. Don't create your own engine;
     bind migrate_engine to your metadata
    """

    table_str = ''
    try:
        meta.bind = migrate_engine
        meta.drop_all(tables=up_tables)
        for table in up_tables:
            table_str = repr(table)
            table.create()
    except Exception:
        LOG.exception(_('Exception while creating table ' + table_str))
        meta.drop_all(tables=up_tables)
        raise


def downgrade(migrate_engine):
    """
     Operations to reverse the above upgrade go here.
    """
    table_str = ''
    try:
        meta.bind = migrate_engine
        down_tables = reversed(up_tables)
        for table in down_tables:
            table_str = repr(table)
            table.drop(checkfirst=True)
    except Exception:
        LOG.exception(_('Exception while deleting table ' + table_str))
        raise
