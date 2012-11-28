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
Maps schema objects to Model classes in module
nova.healthnmon.resourcemodel.healthnmonResourceModel
"""

from sqlalchemy import and_, or_
from sqlalchemy.orm import mapper, relationship
from healthnmon.resourcemodel import healthnmonResourceModel as model
from healthnmon.db.sqlalchemy import manage_healthnmon_db as schema
from sqlalchemy.ext.associationproxy import association_proxy
from healthnmon.resourcemodel.healthnmonResourceModel import MemberSpec_


def map_models():

#    clear_mappers()

    mapper(model.OsProfile, schema.OsProfile)
    mapper(model.Cost, schema.Cost)

    mapper(model.PhysicalServer, schema.PhysicalServer)

    mapper(model.IpProfile, schema.IpProfile)

    mapper(model.VmHost, schema.VmHost, inherits=model.PhysicalServer,
           properties={
           'createEpoch': [schema.PhysicalServer.c.createEpoch,
                           schema.VmHost.c.createEpoch],
           'lastModifiedEpoch': [schema.PhysicalServer.c.lastModifiedEpoch,
                                 schema.VmHost.c.lastModifiedEpoch],
           'deletedEpoch': [schema.PhysicalServer.c.deletedEpoch,
                            schema.VmHost.c.deletedEpoch],
           'resourceManagerId': [schema.PhysicalServer.c.resourceManagerId,
                                 schema.VmHost.c.resourceManagerId],
           'cost': relationship(model.Cost,
                                foreign_keys=schema.PhysicalServer.c.costId),
           'os': relationship(model.OsProfile,
                              foreign_keys=schema.PhysicalServer.c.osId),
           'deleted': [schema.PhysicalServer.c.deleted,
                       schema.VmHost.c.deleted],
           'virtualSwitches': relationship(model.VirtualSwitch,
                                           foreign_keys=schema.VirtualSwitch.c.vmHostId,
                                           primaryjoin=(
                                           and_(
                                               schema.VmHost.c.id == schema.VirtualSwitch.c.vmHostId,
                                           or_(
                                           schema.VirtualSwitch.c.deleted == False, schema.VirtualSwitch.c.deleted == None))),
                                           cascade='all, delete, delete-orphan'),
           'portGroups': relationship(model.PortGroup,
                                      foreign_keys=schema.PortGroup.c.vmHostId,
                                      primaryjoin=(
                                      and_(
                                          schema.VmHost.c.id == schema.PortGroup.c.vmHostId,
                                      or_(
                                      schema.PortGroup.c.deleted == False, schema.PortGroup.c.deleted == None))),
                                      cascade='all, delete, delete-orphan'),
           'ipAddresses': relationship(model.IpProfile,
                                       foreign_keys=schema.IpProfile.c.vmHostId,
                                       cascade='all, delete, delete-orphan'
                                       ),
           })

    mapper(model.Subnet, schema.Subnet, properties={
        'groupIdTypes': relationship(model.GroupIdType,
                                     foreign_keys=schema.GroupIdType.c.subnetId),
        'resourceTags': relationship(model.ResourceTag,
                                     foreign_keys=schema.ResourceTag.c.subnetId),
        'ipAddressRanges': relationship(model.IpAddressRange,
                                        foreign_keys=schema.IpAddressRange.c.subnetId,
                                        cascade='all, delete, delete-orphan'),
        'usedIpAddresses': relationship(model.IpAddress,
                                        foreign_keys=schema.IpAddress.c.subnetId,
                                        cascade='all, delete, delete-orphan'),
        'networkSrc': relationship(SubnetNetworkSource, uselist=True,
                                   primaryjoin=schema.Subnet.c.id
                                   == schema.SubnetNetworkSources.c.subnetId,
                                   cascade='all, delete, delete-orphan'),
        'dnsServer': relationship(SubnetDnsServer, uselist=True,
                                  primaryjoin=schema.Subnet.c.id
                                  == schema.SubnetDnsServers.c.subnetId),
        'dnsSuffixes': relationship(SubnetDnsSearchSuffix,
                                    uselist=True,
                                    primaryjoin=schema.Subnet.c.id
                                    == schema.SubnetDnsSearchSuffixes.c.subnetId),
        'defaultGateway': relationship(SubnetDefaultGateway,
                                       uselist=True, primaryjoin=schema.Subnet.c.id
                                       == schema.SubnetDefaultGateways.c.subnetId,
                                       cascade='all, delete, delete-orphan'),
        'winsServer': relationship(SubnetWinServer, uselist=True,
                                   primaryjoin=schema.Subnet.c.id
                                   == schema.SubnetWinServers.c.subnetId),
        'ntpDateServer': relationship(SubnetNtpDateServer,
                                      uselist=True, primaryjoin=schema.Subnet.c.id
                                      == schema.SubnetNtpDateServers.c.subnetId),
        'deploymentService': relationship(SubnetDeploymentService,
                                          uselist=True, primaryjoin=schema.Subnet.c.id
                                          == schema.SubnetDeploymentServices.c.subnetId),
        'parents': relationship(SubnetParentId, uselist=True,
                                primaryjoin=schema.Subnet.c.id
                                == schema.SubnetParentIds.c.subnetId),
        'childs': relationship(SubnetChildId, uselist=True,
                               primaryjoin=schema.Subnet.c.id
                               == schema.SubnetChildIds.c.subnetId),
        'redundancyPeer': relationship(SubnetRedundancyPeerId,
                                       uselist=True, primaryjoin=schema.Subnet.c.id
                                       == schema.SubnetRedundancyPeerIds.c.subnetId),
    })

    mapper(model.GroupIdType, schema.GroupIdType,
           properties={'networkType': relationship(GroupIdTypeNetworkTypes,
           uselist=True, primaryjoin=schema.GroupIdType.c.id
           == schema.GroupIdTypeNetworkTypes.c.groupTypeId)})

    model.GroupIdType.networkTypes = association_proxy('networkType',
                                                       'networkTypeId')
    mapper(GroupIdTypeNetworkTypes, schema.GroupIdTypeNetworkTypes)

    mapper(model.ResourceTag, schema.ResourceTag)
    mapper(model.IpAddress, schema.IpAddress)
    mapper(model.IpAddressRange, schema.IpAddressRange,
           properties={'startAddress': relationship(model.IpAddress,
           foreign_keys=schema.IpAddressRange.c.startAddressId,
           primaryjoin=schema.IpAddressRange.c.startAddressId
           == schema.IpAddress.c.id),
           'endAddress': relationship(model.IpAddress,
           foreign_keys=schema.IpAddressRange.c.endAddressId,
           primaryjoin=schema.IpAddressRange.c.endAddressId
           == schema.IpAddress.c.id)})

    model.Subnet.networkSources = association_proxy('networkSrc',
                                                    'networkSourceId')
    mapper(SubnetNetworkSource, schema.SubnetNetworkSources)

    model.Subnet.dnsServers = association_proxy('dnsServer',
                                                'dnsServerId')
    mapper(SubnetDnsServer, schema.SubnetDnsServers)
    model.Subnet.defaultGateways = association_proxy('defaultGateway',
                                                     'defaultGatewayId')
    mapper(SubnetDefaultGateway, schema.SubnetDefaultGateways)
    model.Subnet.dnsSearchSuffixes = association_proxy('dnsSuffixes',
                                                      'dnsSuffixId')
    mapper(SubnetDnsSearchSuffix, schema.SubnetDnsSearchSuffixes)
    model.Subnet.winsServers = association_proxy('winsServer',
            'winServerId')
    mapper(SubnetWinServer, schema.SubnetWinServers)
    model.Subnet.ntpDateServers = association_proxy('ntpDateServer',
            'ntpDateServerId')
    mapper(SubnetNtpDateServer, schema.SubnetNtpDateServers)
    model.Subnet.deploymentServices = \
        association_proxy('deploymentService', 'deploymentServiceId')
    mapper(SubnetDeploymentService, schema.SubnetDeploymentServices)
    model.Subnet.parentIds = association_proxy('parents', 'parentId')
    mapper(SubnetParentId, schema.SubnetParentIds)
    model.Subnet.childIds = association_proxy('childs', 'childId')
    mapper(SubnetChildId, schema.SubnetChildIds)
    model.Subnet.redundancyPeerIds = association_proxy('redundancyPeer',
                                                       'redundancyPeerId')
    mapper(SubnetRedundancyPeerId, schema.SubnetRedundancyPeerIds)

    mapper(model.VirtualSwitch, schema.VirtualSwitch,
           properties={
            'portGroups': relationship(model.PortGroup,
                            foreign_keys=schema.PortGroup.c.virtualSwitchId,
                            primaryjoin=(
                                and_(
                                    schema.VirtualSwitch.c.id == schema.PortGroup.c.virtualSwitchId,
                             or_(
                                 schema.PortGroup.c.deleted == False, schema.PortGroup.c.deleted == None))),
                            cascade='all, delete, delete-orphan'),
            'cost': relationship(model.Cost,
                            foreign_keys=schema.VirtualSwitch.c.costId),
            'subnets': relationship(VirtualSwitchSubnetIds,
                            uselist=True, primaryjoin=schema.VirtualSwitch.c.id
                            == schema.VirtualSwitchSubnetIds.c.virtualSwitchId,
                            cascade='all, delete, delete-orphan'),
            'networks': relationship(VirtualSwitchInterfaces,
                            uselist=True, primaryjoin=schema.VirtualSwitch.c.id
                            == schema.NetworkInterfaces.c.vSwitchId,
                            cascade='all, delete, delete-orphan')})

    model.VirtualSwitch.subnetIds = association_proxy('subnets', 'subnetId')

    mapper(VirtualSwitchSubnetIds, schema.VirtualSwitchSubnetIds)
    model.VirtualSwitch.networkInterfaces = association_proxy(
        'networks', 'interfaceId')
    mapper(VirtualSwitchInterfaces, schema.NetworkInterfaces)
    mapper(model.PortGroup, schema.PortGroup,
           properties={
            'type_': schema.PortGroup.c.type,
            'cost': relationship(model.Cost,
                            foreign_keys=schema.PortGroup.c.costId)})

    mapper(model.Vm, schema.Vm, properties={
        'cost': relationship(model.Cost,
                             foreign_keys=schema.Vm.c.costId),
        'os': relationship(model.OsProfile,
                           foreign_keys=schema.Vm.c.osId),
        'ipAddresses': relationship(model.IpProfile,
                                    foreign_keys=schema.IpProfile.c.vmId,
                                    cascade='all, delete, delete-orphan'
                                    ),
        'vmNetAdapters': relationship(model.VmNetAdapter,
                foreign_keys=schema.VmNetAdapter.c.vmId,
                cascade='all, delete, delete-orphan'),
        'vmScsiControllers': relationship(model.VmScsiController,
                foreign_keys=schema.VmScsiController.c.vmId,
                cascade='all, delete, delete-orphan'),
        'vmDisks': relationship(model.VmDisk,
                                foreign_keys=schema.VmDisk.c.vmId,
                                cascade='all, delete, delete-orphan'),
        'vmGenericDevices': relationship(model.VmGenericDevice,
                foreign_keys=schema.VmGenericDevice.c.vmId,
                cascade='all, delete, delete-orphan'),
        'vmGlobalSettings': relationship(model.VmGlobalSettings,
                foreign_keys=schema.Vm.c.globalSettingsId),
        'cpuResourceAllocation': relationship(model.ResourceAllocation,
                foreign_keys=schema.Vm.c.cpuResourceAllocationId,
                primaryjoin=schema.Vm.c.cpuResourceAllocationId
                == schema.ResourceAllocation.c.id),
        'memoryResourceAllocation': relationship(model.ResourceAllocation,
                foreign_keys=schema.Vm.c.memoryResourceAllocationId,
                primaryjoin=schema.Vm.c.memoryResourceAllocationId
                == schema.ResourceAllocation.c.id),
        })

    mapper(model.VmGlobalSettings, schema.VmGlobalSettings)

    mapper(model.VmScsiController, schema.VmScsiController,
           properties={'type_': schema.VmScsiController.c.type})

    mapper(model.VmNetAdapter, schema.VmNetAdapter,
           properties={'ipAdd': relationship(VmNetAdapterIpProfile,
           uselist=True, primaryjoin=schema.VmNetAdapter.c.id
           == schema.VmNetAdapterIpProfiles.c.netAdapterId,
           cascade='all, delete, delete-orphan')})

    model.VmNetAdapter.ipAddresses = association_proxy('ipAdd',
            'ipAddress')
    mapper(VmNetAdapterIpProfile, schema.VmNetAdapterIpProfiles)

    mapper(model.VmDisk, schema.VmDisk)

    mapper(model.VmGenericDevice, schema.VmGenericDevice,
           properties={'properties': relationship(model.Property,
           foreign_keys=schema.VmProperty.c.vmDeviceId,
           cascade='all, delete, delete-orphan')})

    mapper(model.Property, schema.VmProperty)

    mapper(model.ResourceAllocation, schema.ResourceAllocation)
    mapper(model.HostMountPoint, schema.HostMountPoint)
    mapper(model.StorageVolume, schema.StorageVolume,
           properties={'mountPoints': relationship(model.HostMountPoint,
           foreign_keys=schema.HostMountPoint.c.storageVolumeId,
           cascade='all, delete, delete-orphan'),
           'vmDisks': relationship(model.VmDisk,
           foreign_keys=schema.VmDisk.c.storageVolumeId,
           cascade='all, delete, delete-orphan')})


# The below are mapper classes for list tables.

class VirtualSwitchSubnetIds(object):

    member_data_items_ = {'subnetId': MemberSpec_('subnetId',
                          'xs:string', 0),
                          'virtualSwitchId': MemberSpec_('virtualSwitchId',
                                                         'xs:string', 0)}

    def __init__(self, subnetId=None, virtualSwitchId=None):
        self.subnetId = subnetId
        self.virtualSwitchId = virtualSwitchId


class VirtualSwitchInterfaces(object):

    member_data_items_ = {'interfaceId': MemberSpec_('interfaceId',
                          'xs:string', 0),
                          'vSwitchId': MemberSpec_('vSwitchId',
                          'xs:string', 0)}

    def __init__(self, interfaceId=None, vSwitchId=None):
        self.interfaceId = interfaceId
        self.vSwitchId = vSwitchId


class SubnetNetworkSource(object):

    member_data_items_ = \
        {'networkSourceId': MemberSpec_('networkSourceId', 'xs:string',
         0), 'subnetId': MemberSpec_('subnetId', 'xs:string', 0)}

    def __init__(self, networkSourceId=None, subnetId=None):
        self.networkSourceId = networkSourceId
        self.subnetId = subnetId


class SubnetDnsServer(object):

    member_data_items_ = {'dnsServerId': MemberSpec_('dnsServerId',
                          'xs:string', 0),
                          'subnetId': MemberSpec_('subnetId',
                          'xs:string', 0)}

    def __init__(self, dnsServerId=None, subnetId=None):
        self.dnsServerId = dnsServerId
        self.subnetId = subnetId


class SubnetDnsSearchSuffix(object):

    member_data_items_ = {'dnsSuffixId': MemberSpec_('dnsSuffixId',
                          'xs:string', 0),
                          'subnetId': MemberSpec_('subnetId',
                          'xs:string', 0)}

    def __init__(self, dnsSuffixId=None, subnetId=None):
        self.dnsSuffixId = dnsSuffixId
        self.subnetId = subnetId


class SubnetDefaultGateway(object):

    member_data_items_ = \
        {'defaultGatewayId': MemberSpec_('defaultGatewayId', 'xs:string',
                 0), 'subnetId': MemberSpec_('subnetId', 'xs:string', 0)}

    def __init__(self, defaultGatewayId=None, subnetId=None):
        self.defaultGatewayId = defaultGatewayId
        self.subnetId = subnetId


class SubnetWinServer(object):

    member_data_items_ = {'winServerId': MemberSpec_('winServerId',
                          'xs:string', 0),
                          'subnetId': MemberSpec_('subnetId',
                          'xs:string', 0)}

    def __init__(self, winServerId=None, subnetId=None):
        self.winServerId = winServerId
        self.subnetId = subnetId


class SubnetNtpDateServer(object):

    member_data_items_ = \
        {'ntpDateServerId': MemberSpec_('ntpDateServerId', 'xs:string',
         0), 'subnetId': MemberSpec_('subnetId', 'xs:string', 0)}

    def __init__(self, ntpDateServerId=None, subnetId=None):
        self.ntpDateServerId = ntpDateServerId
        self.subnetId = subnetId


class SubnetDeploymentService(object):

    member_data_items_ = \
        {'deploymentServiceId': MemberSpec_('deploymentServiceId',
         'xs:string', 0), 'subnetId': MemberSpec_('subnetId',
         'xs:string', 0)}

    def __init__(self, deploymentServiceId=None, subnetId=None):
        self.deploymentServiceId = deploymentServiceId
        self.subnetId = subnetId


class SubnetParentId(object):

    member_data_items_ = {'parentId': MemberSpec_('parentId',
                          'xs:string', 0),
                          'subnetId': MemberSpec_('subnetId',
                          'xs:string', 0)}

    def __init__(self, parentId=None, subnetId=None):
        self.parentId = parentId
        self.subnetId = subnetId


class SubnetChildId(object):

    member_data_items_ = {'childId': MemberSpec_('childId', 'xs:string',
                           0), 'subnetId': MemberSpec_('subnetId',
                          'xs:string', 0)}

    def __init__(self, childId=None, subnetId=None):
        self.childId = childId
        self.subnetId = subnetId


class SubnetRedundancyPeerId(object):

    member_data_items_ = \
        {'redundancyPeerId': MemberSpec_('redundancyPeerId', 'xs:string',
         0), 'subnetId': MemberSpec_('subnetId', 'xs:string', 0)}

    def __init__(self, redundancyPeerId=None, subnetId=None):
        self.redundancyPeerId = redundancyPeerId
        self.subnetId = subnetId


class GroupIdTypeNetworkTypes(object):

    member_data_items_ = {'networkTypeId': MemberSpec_('networkTypeId',
                          'xs:string', 0),
                          'groupTypeId': MemberSpec_('groupTypeId',
                          'xs:string', 0)}

    def __init__(self, networkTypeId=None, groupTypeId=None):
        self.networkTypeId = networkTypeId
        self.groupTypeId = groupTypeId


class VmNetAdapterIpProfile(object):

    member_data_items_ = {'ipAddress': MemberSpec_('ipAddress',
                          'xs:string', 0),
                          'netAdapterId': MemberSpec_('netAdapterId',
                          'xs:string', 0)}

    def __init__(self, ipAddress=None, netAdapterId=None):
        self.ipAddress = ipAddress
        self.netAdapterId = netAdapterId
