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

from healthnmon.db import api as healthnmon_db_api
from healthnmon.resourcemodel.healthnmonResourceModel import Subnet
from healthnmon.resourcemodel.healthnmonResourceModel import VirtualSwitch
from healthnmon.resourcemodel.healthnmonResourceModel import GroupIdType
from healthnmon.resourcemodel.healthnmonResourceModel import IpAddress
from healthnmon.resourcemodel.healthnmonResourceModel import IpAddressRange
from healthnmon import test
from nova.openstack.common.db.sqlalchemy import session as db_session
from nova.context import get_admin_context
from healthnmon.constants import DbConstants
import time
from healthnmon import utils
from healthnmon.tests import utils as test_utils
from healthnmon.utils import XMLUtils


class SubnetDbApiTestCase(test.TestCase):

    def setUp(self):
        super(SubnetDbApiTestCase, self).setUp()
#        self.mock = mox.Mox()
        self.admin_context = get_admin_context()

    def tearDown(self):
        super(SubnetDbApiTestCase, self).tearDown()
        # self.mock.stubs.UnsetAll()

    def __create_subnet(self, **kwargs):
        subnet = Subnet()
        if kwargs is not None:
            for field in kwargs:
                setattr(subnet, field, kwargs[field])
        healthnmon_db_api.subnet_save(self.admin_context, subnet)
        return subnet

    def _create_ip_range_from_xml(self, subnet_id, network_name,
                                  ip_address, start_ip, end_ip):
        lib_utils = XMLUtils()
        net_xml = '<network><name>' + \
            network_name + '</name><forward mode=\'nat\'/><ip address=\' ' + \
            ip_address + \
            '\' netmask=\'255.255.255.0\'><dhcp><range start=\'' + \
            start_ip + '\' end=\'' + end_ip + '\'/>''</dhcp></ip></network>'

        ipRange = IpAddressRange()
        if lib_utils.parseXML(net_xml, '//network/ip/dhcp') is not None:
                startIpAddress = IpAddress()
                startIpAddress.set_address(lib_utils.parseXMLAttributes(
                    net_xml, '//network/ip/dhcp/range', 'start'))
                ipRange.set_id(startIpAddress.get_address())
                startIpAddress.set_id(startIpAddress.get_address())
                startIpAddress.set_allocationType('DHCP')
                ipRange.set_startAddress(startIpAddress)
                endIpAddress = IpAddress()
                endIpAddress.set_address(lib_utils.parseXMLAttributes(
                    net_xml, '//network/ip/dhcp/range', 'end'))
                endIpAddress.set_id(endIpAddress.get_address())
                endIpAddress.set_allocationType('DHCP')
                ipRange.set_endAddress(endIpAddress)
                ipRange.set_allocationType('DHCP')
        else:
                ipRange.set_id(subnet_id + '_AUTO_STATIC')
                ipRange.set_allocationType('AUTO_STATIC')
        return ipRange

    def test_subnet_save(self):
        subnet = Subnet()
        subnet.set_id('subnet-01')
        subnet.set_name('subnet-01')
        groupIdType = GroupIdType()
        groupIdType.set_id('groupId-01')
        groupIdType.add_networkTypes('MAPPED')
        groupIdType.add_networkTypes('TUNNEL')
        subnet.add_groupIdTypes(groupIdType)
        subnet.set_networkAddress('1.1.1.1')
        subnet.set_networkMask('255.255.255.0')
        subnet.add_networkSources('VS_NETWORK')
        subnet.set_ipType('IPV4')

        subnet.set_isPublic(True)
        subnet.set_isShareable(True)
        subnet.add_dnsServers('test-dns01')
        subnet.set_dnsDomain('test_Domain')
        subnet.add_dnsSearchSuffixes('dnsSearchSuffixes')
        subnet.add_defaultGateways('defaultGateways')
        subnet.set_msDomainName('msDomainName')
        subnet.set_msDomainType('DOMAIN')
        subnet.add_winsServers('winsServers')
        subnet.add_ntpDateServers('ntpDateServers')
        subnet.set_vlanId('1')
        subnet.set_isBootNetwork(True)
        subnet.add_deploymentServices('deploymentServices')
        subnet.add_parentIds('parentIds')
        subnet.add_childIds('childIds')
        subnet.set_isTrunk(True)
        subnet.add_redundancyPeerIds('redundancyPeerIds')
        subnet.set_redundancyMasterId('redundancyMasterId')
        subnet.set_isNativeVlan(False)
        userIp = IpAddress()
        userIp.set_id('10.10.20.1')
        userIp.set_address('10.10.20.1')
        subnet.add_usedIpAddresses(userIp)
        ipRange = self._create_ip_range_from_xml(subnet.get_id(
        ), 'network1', '10.10.10.1', '10.10.10.1', '10.10.10.2')
        subnet.add_ipAddressRanges(ipRange)

        healthnmon_db_api.subnet_save(self.admin_context, subnet)
        subnets = \
            healthnmon_db_api.subnet_get_by_ids(self.admin_context,
                                                ['subnet-01'])
        self.assertFalse(subnets is None,
                         'subnet all returned a none list')
        self.assertTrue(len(subnets) == 1,
                        'subnet all returned invalid number of list')

        indexOfThesubnet = -1
        for subn in subnets:
            if subn.get_id() == subnet.get_id():
                indexOfThesubnet = subnets.index(subn)
                break

        self.assertTrue(subnets[indexOfThesubnet].get_id()
                        == 'subnet-01', 'Subnet id mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_name()
                        == 'subnet-01', 'Subnet name mismatch')

        groupIdType = subnets[indexOfThesubnet].get_groupIdTypes()[0]
        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(groupIdType.get_networkTypes(
        )[0] == 'MAPPED', 'Network Type mismatch')
        self.assertTrue(groupIdType.get_networkTypes(
        )[1] == 'TUNNEL', 'Network Type mismatch')

        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkAddress(
        ) == '1.1.1.1', 'Network Address mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkMask(
        ) == '255.255.255.0', 'Subnet mask mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkSources(
        )[0] == 'VS_NETWORK', 'Network Sources mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_ipType()
                        == 'IPV4', 'Ip Type mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_isPublic(),
                        'Subnet isPublic returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_isShareable(),
                        'Subnet isShareable returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_dnsServers(
        )[0] == 'test-dns01', 'DnsServer mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_dnsDomain(
        ) == 'test_Domain', 'DnsDomain mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_dnsSearchSuffixes(
        )[0] == 'dnsSearchSuffixes', 'Subnet isShareable returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_defaultGateways(
        )[0] == 'defaultGateways', 'defaultGateways mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_msDomainName(
        ) == 'msDomainName', 'msDomainName mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_msDomainType(
        ) == 'DOMAIN', 'DOMAIN mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_winsServers(
        )[0] == 'winsServers', 'winsServers mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_ntpDateServers(
        )[0] == 'ntpDateServers', 'ntpDateServers mismatch')
        self.assertTrue(
            subnets[indexOfThesubnet].get_vlanId() == '1', 'vlanId mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_isBootNetwork(),
                        'IsbootNetwork returned False')
        self.assertTrue(subnets[indexOfThesubnet].get_deploymentServices(
        )[0] == 'deploymentServices', 'deploymentServices mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_parentIds(
        )[0] == 'parentIds', 'parentIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_childIds()[0]
                        == 'childIds', 'childIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_isTrunk(),
                        'IsTrunk returned False')

        self.assertTrue(subnets[indexOfThesubnet].get_redundancyPeerIds(
        )[0] == 'redundancyPeerIds', 'redundancyPeerIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_redundancyMasterId(
        ) == 'redundancyMasterId', 'redundancyMasterId mismatch')
        self.assertFalse(subnets[indexOfThesubnet].get_isNativeVlan(),
                         'IsNativePlan should be false')

    def test_subnet_save_update(self):
        subnet = Subnet()
        subnet.set_id('subnet-01')
        subnet.set_name('subnet-01')
        subnet.set_networkAddress('1.1.1.1')
        subnet.set_networkMask('255.255.255.0')
        subnet.add_networkSources('VS_NETWORK')
        subnet.add_dnsServers('test-dns01')
        userIp1 = IpAddress()
        userIp1.set_id('10.10.20.1')
        userIp1.set_address('10.10.20.1')
        subnet.add_usedIpAddresses(userIp1)
        range_id_R1 = subnet.get_id() + "_R1"
        ipRange_R1 = self._create_ip_range_from_xml(
            range_id_R1, 'network1', '10.10.10.1', '10.10.10.1', '10.10.10.2')
        subnet.add_ipAddressRanges(ipRange_R1)
        userIp2 = IpAddress()
        userIp2.set_id('10.10.20.5')
        userIp2.set_address('10.10.20.5')
        subnet.add_usedIpAddresses(userIp2)
        range_id_R2 = subnet.get_id() + "_R2"
        ipRange_R2 = self._create_ip_range_from_xml(
            range_id_R2, 'network2', '10.10.10.5', '10.10.10.5', '10.10.10.7')
        subnet.add_ipAddressRanges(ipRange_R2)
        healthnmon_db_api.subnet_save(self.admin_context, subnet)

        subnet = healthnmon_db_api.subnet_get_by_ids(
            self.admin_context, [subnet.id])[0]
        groupIdType = GroupIdType()
        groupIdType.set_id('groupId-01')
        groupIdType.add_networkTypes('MAPPED')
        groupIdType.add_networkTypes('TUNNEL')
        subnet.add_groupIdTypes(groupIdType)
        subnet.set_ipType('IPV4')
        subnet.set_isPublic(True)
        subnet.set_isShareable(True)
        subnet.set_dnsDomain('test_Domain')
        subnet.add_dnsSearchSuffixes('dnsSearchSuffixes')
        subnet.add_defaultGateways('defaultGateways')
        subnet.set_msDomainName('msDomainName')
        subnet.set_msDomainType('DOMAIN')
        subnet.add_winsServers('winsServers')
        subnet.add_ntpDateServers('ntpDateServers')
        subnet.set_vlanId('1')
        subnet.set_isBootNetwork(True)
        subnet.add_deploymentServices('deploymentServices')
        subnet.add_parentIds('parentIds')
        subnet.add_childIds('childIds')
        subnet.set_isTrunk(True)
        subnet.add_redundancyPeerIds('redundancyPeerIds')
        subnet.set_redundancyMasterId('redundancyMasterId')
        subnet.set_isNativeVlan(False)
        userIp3 = IpAddress()
        userIp3.set_id('10.10.20.11')
        userIp3.set_address('10.10.20.11')
        usedIps = [userIp2, userIp3]
        subnet.set_usedIpAddresses([])
        subnet.set_usedIpAddresses(usedIps)

        range_id_R3 = subnet.get_id() + "_R3"
        ipRange_R3 = \
            self._create_ip_range_from_xml(range_id_R3,
                                           'network3',
                                           '10.10.10.11',
                                           '10.10.10.11', '10.10.10.12')
        ipRanges = [ipRange_R2, ipRange_R3]
        subnet.set_ipAddressRanges([])
        subnet.set_ipAddressRanges(ipRanges)
        healthnmon_db_api.subnet_save(self.admin_context, subnet)

        subnets = \
            healthnmon_db_api.subnet_get_by_ids(self.admin_context,
                                                ['subnet-01'])  # for update

        self.assertFalse(subnets is None,
                         'subnet all returned a none list')
        self.assertTrue(len(subnets) == 1,
                        'subnet all returned invalid number of list')

        indexOfThesubnet = -1
        for subn in subnets:
            if subn.get_id() == subnet.get_id():
                indexOfThesubnet = subnets.index(subn)
                break

        self.assertTrue(subnets[indexOfThesubnet].get_id()
                        == 'subnet-01', 'Subnet id mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_name()
                        == 'subnet-01', 'Subnet name mismatch')

        groupIdType = subnets[indexOfThesubnet].get_groupIdTypes()[0]
        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(groupIdType.get_networkTypes(
        )[0] == 'MAPPED', 'Network Type mismatch')
        self.assertTrue(groupIdType.get_networkTypes(
        )[1] == 'TUNNEL', 'Network Type mismatch')

        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkAddress(
        ) == '1.1.1.1', 'Network Address mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkMask(
        ) == '255.255.255.0', 'Subnet mask mismatch')
        self.assertFalse(len(subnets[indexOfThesubnet].get_networkSources(
        )) == 0, 'Network Sources didn\'t get updated')
        self.assertTrue(subnets[indexOfThesubnet].get_networkSources(
        )[0] == 'VS_NETWORK', 'Network Sources mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_dnsServers(
        )[0] == 'test-dns01', 'DnsServer mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_ipType()
                        == 'IPV4', 'Ip Type mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_isPublic(),
                        'Subnet isPublic returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_isShareable(),
                        'Subnet isShareable returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_dnsDomain(
        ) == 'test_Domain', 'DnsDomain mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_dnsSearchSuffixes(
        )[0] == 'dnsSearchSuffixes', 'Subnet isShareable returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_defaultGateways(
        )[0] == 'defaultGateways', 'defaultGateways mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_msDomainName(
        ) == 'msDomainName', 'msDomainName mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_msDomainType(
        ) == 'DOMAIN', 'DOMAIN mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_winsServers(
        )[0] == 'winsServers', 'winsServers mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_ntpDateServers(
        )[0] == 'ntpDateServers', 'ntpDateServers mismatch')
        self.assertTrue(
            subnets[indexOfThesubnet].get_vlanId() == '1', 'vlanId mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_isBootNetwork(),
                        'IsbootNetwork returned False')
        self.assertTrue(subnets[indexOfThesubnet].get_deploymentServices(
        )[0] == 'deploymentServices', 'deploymentServices mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_parentIds(
        )[0] == 'parentIds', 'parentIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_childIds()[0]
                        == 'childIds', 'childIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_isTrunk(),
                        'IsTrunk returned False')

        self.assertTrue(subnets[indexOfThesubnet].get_redundancyPeerIds(
        )[0] == 'redundancyPeerIds', 'redundancyPeerIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_redundancyMasterId(
        ) == 'redundancyMasterId', 'redundancyMasterId mismatch')
        self.assertFalse(subnets[indexOfThesubnet].get_isNativeVlan(),
                         'IsNativePlan should be false')

    def test_subnet_get_all(self):
        subnet = Subnet()
        subnet.set_id('subnet-01')
        subnet.set_name('subnet-01')
        groupIdType = GroupIdType()
        groupIdType.set_id('groupId-01')
        groupIdType.add_networkTypes('MAPPED')
        groupIdType.add_networkTypes('TUNNEL')
        subnet.add_groupIdTypes(groupIdType)
        subnet.set_networkAddress('1.1.1.1')
        subnet.set_networkMask('255.255.255.0')
        subnet.add_networkSources('VS_NETWORK')
        subnet.set_ipType('IPV4')
        subnet.set_isPublic(True)
        subnet.set_isShareable(True)
        subnet.add_dnsServers('test-dns01')
        subnet.set_dnsDomain('test_Domain')
        subnet.add_dnsSearchSuffixes('dnsSearchSuffixes')
        subnet.add_defaultGateways('defaultGateways')
        subnet.set_msDomainName('msDomainName')
        subnet.set_msDomainType('DOMAIN')
        subnet.add_winsServers('winsServers')
        subnet.add_ntpDateServers('ntpDateServers')
        subnet.set_vlanId(1)
        subnet.set_isBootNetwork(True)
        subnet.add_deploymentServices('deploymentServices')
        subnet.add_parentIds('parentIds')
        subnet.add_childIds('childIds')
        subnet.set_isTrunk(True)
        subnet.add_redundancyPeerIds('redundancyPeerIds')
        subnet.set_redundancyMasterId('redundancyMasterId')
        subnet.set_isNativeVlan(False)
        healthnmon_db_api.subnet_save(self.admin_context, subnet)
        subnets = healthnmon_db_api.subnet_get_all(self.admin_context)

        self.assertFalse(subnets is None,
                         'subnet all returned a none list')
        self.assertTrue(len(subnets) == 1,
                        'subnet all returned invalid number of list')

        indexOfThesubnet = -1
        for subn in subnets:
            if subn.get_id() == subnet.get_id():
                indexOfThesubnet = subnets.index(subn)
                break

        self.assertTrue(subnets[indexOfThesubnet].get_id()
                        == 'subnet-01', 'Subnet id mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_name()
                        == 'subnet-01', 'Subnet name mismatch')

        groupIdType = subnets[indexOfThesubnet].get_groupIdTypes()[0]
        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(groupIdType.get_networkTypes(
        )[0] == 'MAPPED', 'Network Type mismatch')
        self.assertTrue(groupIdType.get_networkTypes(
        )[1] == 'TUNNEL', 'Network Type mismatch')

        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkAddress(
        ) == '1.1.1.1', 'Network Address mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkMask(
        ) == '255.255.255.0', 'Subnet mask mismatch')
        self.assertFalse(len(subnets[indexOfThesubnet].get_networkSources(
        )) == 0, 'Network Sources didn\'t get updated')
        self.assertTrue(subnets[indexOfThesubnet].get_networkSources(
        )[0] == 'VS_NETWORK', 'Network Sources mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_ipType()
                        == 'IPV4', 'Ip Type mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_isPublic(),
                        'Subnet isPublic returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_isShareable(),
                        'Subnet isShareable returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_dnsServers(
        )[0] == 'test-dns01', 'DnsServer mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_dnsDomain(
        ) == 'test_Domain', 'DnsDomain mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_dnsSearchSuffixes(
        )[0] == 'dnsSearchSuffixes', 'Subnet isShareable returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_defaultGateways(
        )[0] == 'defaultGateways', 'defaultGateways mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_msDomainName(
        ) == 'msDomainName', 'msDomainName mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_msDomainType(
        ) == 'DOMAIN', 'DOMAIN mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_winsServers(
        )[0] == 'winsServers', 'winsServers mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_ntpDateServers(
        )[0] == 'ntpDateServers', 'ntpDateServers mismatch')
        self.assertTrue(
            subnets[indexOfThesubnet].get_vlanId() == '1', 'vlanId mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_isBootNetwork(),
                        'IsbootNetwork returned False')
        self.assertTrue(subnets[indexOfThesubnet].get_deploymentServices(
        )[0] == 'deploymentServices', 'deploymentServices mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_parentIds(
        )[0] == 'parentIds', 'parentIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_childIds()[0]
                        == 'childIds', 'childIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_isTrunk(),
                        'IsTrunk returned False')

        self.assertTrue(subnets[indexOfThesubnet].get_redundancyPeerIds(
        )[0] == 'redundancyPeerIds', 'redundancyPeerIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_redundancyMasterId(
        ) == 'redundancyMasterId', 'redundancyMasterId mismatch')
        self.assertFalse(subnets[indexOfThesubnet].get_isNativeVlan(),
                         'IsNativePlan should be false')

    def test_subnet_get_by_id(self):
        subnet = Subnet()
        subnet.set_id('subnet-01')
        subnet.set_name('subnet-01')
        groupIdType = GroupIdType()
        groupIdType.set_id('groupId-01')
        groupIdType.add_networkTypes('MAPPED')
        groupIdType.add_networkTypes('TUNNEL')
        subnet.add_groupIdTypes(groupIdType)
        subnet.set_networkAddress('1.1.1.1')
        subnet.set_networkMask('255.255.255.0')
        subnet.add_networkSources('VS_NETWORK')
        subnet.set_ipType('IPV4')
        subnet.set_isPublic(True)
        subnet.set_isShareable(True)
        subnet.add_dnsServers('test-dns01')
        subnet.set_dnsDomain('test_Domain')
        subnet.add_dnsSearchSuffixes('dnsSearchSuffixes')
        subnet.add_defaultGateways('defaultGateways')
        subnet.set_msDomainName('msDomainName')
        subnet.set_msDomainType('DOMAIN')
        subnet.add_winsServers('winsServers')
        subnet.add_ntpDateServers('ntpDateServers')
        subnet.set_vlanId(1)
        subnet.set_isBootNetwork(True)
        subnet.add_deploymentServices('deploymentServices')
        subnet.add_parentIds('parentIds')
        subnet.add_childIds('childIds')
        subnet.set_isTrunk(True)
        subnet.add_redundancyPeerIds('redundancyPeerIds')
        subnet.set_redundancyMasterId('redundancyMasterId')
        subnet.set_isNativeVlan(False)
        healthnmon_db_api.subnet_save(self.admin_context, subnet)
        subnets = \
            healthnmon_db_api.subnet_get_by_ids(self.admin_context,
                                                [subnet.id])
        self.assertFalse(subnets is None,
                         'subnet all returned a none list')
        self.assertTrue(len(subnets) == 1,
                        'subnet all returned invalid number of list')

        indexOfThesubnet = -1
        for subn in subnets:
            if subn.get_id() == subnet.get_id():
                indexOfThesubnet = subnets.index(subn)
                break

        self.assertTrue(subnets[indexOfThesubnet].get_id()
                        == 'subnet-01', 'Subnet id mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_name()
                        == 'subnet-01', 'Subnet name mismatch')

        groupIdType = subnets[indexOfThesubnet].get_groupIdTypes()[0]
        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(groupIdType.get_networkTypes(
        )[0] == 'MAPPED', 'Network Type mismatch')
        self.assertTrue(groupIdType.get_networkTypes(
        )[1] == 'TUNNEL', 'Network Type mismatch')

        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(
            groupIdType.get_id() == 'groupId-01', 'Group id mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkAddress(
        ) == '1.1.1.1', 'Network Address mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_networkMask(
        ) == '255.255.255.0', 'Subnet mask mismatch')
        self.assertFalse(len(subnets[indexOfThesubnet].get_networkSources(
        )) == 0, 'Network Sources didn\'t get updated')
        self.assertTrue(subnets[indexOfThesubnet].get_networkSources(
        )[0] == 'VS_NETWORK', 'Network Sources mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_ipType()
                        == 'IPV4', 'Ip Type mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_isPublic(),
                        'Subnet isPublic returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_isShareable(),
                        'Subnet isShareable returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_dnsServers(
        )[0] == 'test-dns01', 'DnsServer mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_dnsDomain(
        ) == 'test_Domain', 'DnsDomain mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_dnsSearchSuffixes(
        )[0] == 'dnsSearchSuffixes', 'Subnet isShareable returned false')
        self.assertTrue(subnets[indexOfThesubnet].get_defaultGateways(
        )[0] == 'defaultGateways', 'defaultGateways mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_msDomainName(
        ) == 'msDomainName', 'msDomainName mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_msDomainType(
        ) == 'DOMAIN', 'DOMAIN mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_winsServers(
        )[0] == 'winsServers', 'winsServers mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_ntpDateServers(
        )[0] == 'ntpDateServers', 'ntpDateServers mismatch')
        self.assertTrue(
            subnets[indexOfThesubnet].get_vlanId() == '1', 'vlanId mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_isBootNetwork(),
                        'IsbootNetwork returned False')
        self.assertTrue(subnets[indexOfThesubnet].get_deploymentServices(
        )[0] == 'deploymentServices', 'deploymentServices mismatch')

        self.assertTrue(subnets[indexOfThesubnet].get_parentIds(
        )[0] == 'parentIds', 'parentIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_childIds()[0]
                        == 'childIds', 'childIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_isTrunk(),
                        'IsTrunk returned False')

        self.assertTrue(subnets[indexOfThesubnet].get_redundancyPeerIds(
        )[0] == 'redundancyPeerIds', 'redundancyPeerIds mismatch')
        self.assertTrue(subnets[indexOfThesubnet].get_redundancyMasterId(
        ) == 'redundancyMasterId', 'redundancyMasterId mismatch')
        self.assertFalse(subnets[indexOfThesubnet].get_isNativeVlan(),
                         'IsNativePlan should be false')

    def test_subnet_delete(self):
        subnet = Subnet()
        subnet.set_id('subnet-01')
        subnet.set_name('subnet-01')
        subnet.set_networkAddress('1.1.1.1')
        subnet.set_networkMask('255.255.255.0')
        subnet.add_networkSources('VS_NETWORK')
        subnet.set_ipType('IPV4')
        subnet.set_isPublic(True)
        subnet.set_isShareable(True)
        subnet.add_dnsServers('test-dns01')
        subnet.set_dnsDomain('test_Domain')
        subnet.add_dnsSearchSuffixes('dnsSearchSuffixes')
        subnet.add_defaultGateways('defaultGateways')
        subnet.set_msDomainName('msDomainName')
        subnet.set_msDomainType('WORKGROUP')
        subnet.add_winsServers('winsServers')
        subnet.add_ntpDateServers('ntpDateServers')
        subnet.set_vlanId(1)
        subnet.set_isBootNetwork(True)
        subnet.add_deploymentServices('deploymentServices')
        subnet.add_parentIds('parentIds')
        subnet.add_childIds('childIds')
        subnet.set_isTrunk(True)
        subnet.add_redundancyPeerIds('redundancyPeerIds')
        subnet.set_redundancyMasterId('redundancyMasterId')
        subnet.set_isNativeVlan(False)
        userIp = IpAddress()
        userIp.set_id('10.10.20.1')
        userIp.set_address('10.10.20.1')
        subnet.add_usedIpAddresses(userIp)
        ipRange = self._create_ip_range_from_xml(subnet.get_id(
        ), 'network1', '10.10.10.1', '10.10.10.1', '10.10.10.2')
        subnet.add_ipAddressRanges(ipRange)
        healthnmon_db_api.subnet_save(self.admin_context, subnet)

        subnet2 = Subnet()
        subnet2.set_id('subnet-02')
        subnet2.set_name('subnet-02')
        healthnmon_db_api.subnet_save(self.admin_context, subnet2)

        vSwitch = VirtualSwitch()
        vSwitch.set_id('vs-01')
        vSwitch.set_name('vs-01')
        vSwitch.add_subnetIds('subnet-01')
        vSwitch.add_subnetIds('subnet-02')
        healthnmon_db_api.virtual_switch_save(self.admin_context,
                                              vSwitch)
        healthnmon_db_api.subnet_delete_by_ids(self.admin_context,
                                               [subnet.id])
        subnets = healthnmon_db_api.subnet_get_by_ids(self.admin_context,
                                                      [subnet.id])

        self.assertTrue(subnets is None or len(subnets) == 0,
                        'subnet deleted')

    def test_subnet_save_none(self):
        self.assertTrue(healthnmon_db_api.subnet_save(
            self.admin_context, None) is None, 'No subnet should be saved')

    def test_subnet_get_by_id_none(self):
        self.assertTrue(healthnmon_db_api.subnet_get_by_ids(
            self.admin_context, None) is None, 'No subnet should be returned')

    def test_subnet_delete_none(self):
        self.assertTrue(
            healthnmon_db_api.subnet_delete_by_ids(
                self.admin_context,
                None) is None, 'No subnet to be deleted')

    def test_subnet_save_throw_exception(self):
        self.assertRaises(Exception, healthnmon_db_api.subnet_save,
                          self.admin_context, Subnet())

    def test_subnet_get_ids_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.subnet_get_by_ids,
                          self.admin_context, ['subnet-01'])

    def test_subnet_get_all_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, healthnmon_db_api.subnet_get_all,
                          self.admin_context)

    def test_subnet_delete_exc(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.subnet_delete_by_ids,
                          self.admin_context, ['test1'])

    def test_subnet_get_all_by_filters_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.subnet_get_all_by_filters,
                          self.admin_context, {}, 'id', 'asc')

    def test_subnet_get_all_by_filters(self):
        # Create Subnets
        subnet_ids = ('SN1', 'SN2')
        subnet_names = ('name1', 'name2')
        for i in range(len(subnet_ids)):
            self.__create_subnet(id=subnet_ids[i], name=subnet_names[i])
        # Query with filter
        filters = {'name': subnet_names[1]}
        subnets = healthnmon_db_api. \
            subnet_get_all_by_filters(self.admin_context, filters,
                                      'id', DbConstants.ORDER_ASC)
        self.assert_(subnets is not None)
        self.assert_(len(subnets) == 1)
        self.assert_(subnets[0] is not None)
        self.assert_(subnets[0].id == subnet_ids[1])

    def test_subnet_get_all_by_filters_deleted(self):
        # Create Subnets
        subnet_ids = ('SN1', 'SN2')
        subnet_names = ('name1', 'name2')
        for i in range(len(subnet_ids)):
            self.__create_subnet(id=subnet_ids[i], name=subnet_names[i])
        # Delete one subnet
        healthnmon_db_api.subnet_delete_by_ids(
            self.admin_context, [subnet_ids[0]])
        # Query with filter
        filters = {'deleted': 'true'}
        subnets = healthnmon_db_api. \
            subnet_get_all_by_filters(self.admin_context, filters,
                                      'id', DbConstants.ORDER_ASC)
        self.assert_(subnets is not None)
        self.assert_(len(subnets) == 1)
        self.assert_(subnets[0] is not None)
        self.assert_(subnets[0].id == subnet_ids[0])

    def test_subnet_get_all_by_filters_not_deleted(self):
        # Create Subnets
        subnet_ids = ('SN1', 'SN2')
        subnet_names = ('name1', 'name2')
        for i in range(len(subnet_ids)):
            self.__create_subnet(id=subnet_ids[i], name=subnet_names[i])
        # Delete one subnet
        healthnmon_db_api.subnet_delete_by_ids(
            self.admin_context, [subnet_ids[0]])
        # Query with filter
        filters = {'deleted': False}
        subnets = healthnmon_db_api. \
            subnet_get_all_by_filters(self.admin_context, filters,
                                      'id', DbConstants.ORDER_ASC)
        self.assert_(subnets is not None)
        self.assert_(len(subnets) == 1)
        self.assert_(subnets[0] is not None)
        self.assert_(subnets[0].id == subnet_ids[1])

    def test_subnet_get_all_by_filters_changessince(self):
        # Create Subnets
        subnet_ids = ('SN1', 'SN2', 'SN3')
        subnet_names = ('name1', 'name2', 'name3')
        for i in range(len(subnet_ids)):
            self.__create_subnet(id=subnet_ids[i], name=subnet_names[i])
        created_time = long(time.time() * 1000L)
        # Wait for 1 sec and update second subnet and delete third subnet
        time.sleep(1)
        second_subnet = healthnmon_db_api. \
            subnet_get_by_ids(self.admin_context, [subnet_ids[1]])[0]
        second_subnet.name = 'New name'
        healthnmon_db_api.subnet_save(self.admin_context, second_subnet)
        healthnmon_db_api.subnet_delete_by_ids(
            self.admin_context, [subnet_ids[2]])
        # Query with filter
        expected_updated_ids = [subnet_ids[1], subnet_ids[2]]
        filters = {'changes-since': created_time}
        subnets = healthnmon_db_api. \
            subnet_get_all_by_filters(self.admin_context, filters,
                                      None, None)
        self.assert_(subnets is not None)
        self.assert_(len(subnets) == 2)
        for subnet in subnets:
            self.assert_(subnet is not None)
            self.assert_(subnet.id in expected_updated_ids)

    def test_subnet_get_all_by_filters_sort_asc(self):
        # Create Subnets
        subnet_ids = ('SN1', 'SN2')
        subnet_names = ('name1', 'name2')
        for i in range(len(subnet_ids)):
            self.__create_subnet(id=subnet_ids[i], name=subnet_names[i])
        # Query with sort
        subnets = healthnmon_db_api. \
            subnet_get_all_by_filters(self.admin_context, None,
                                      'name', DbConstants.ORDER_ASC)
        self.assert_(subnets is not None)
        self.assert_(len(subnets) == 2)
        self.assert_(subnets[0] is not None)
        self.assert_(subnets[0].id == subnet_ids[0])
        self.assert_(subnets[1] is not None)
        self.assert_(subnets[1].id == subnet_ids[1])

    def test_subnet_get_all_by_filters_sort_desc(self):
        # Create Subnets
        subnet_ids = ('SN1', 'SN2')
        subnet_names = ('name1', 'name2')
        for i in range(len(subnet_ids)):
            self.__create_subnet(id=subnet_ids[i], name=subnet_names[i])
        # Query with sort
        subnets = healthnmon_db_api. \
            subnet_get_all_by_filters(self.admin_context,
                                      {'name': subnet_names},
                                      'name', DbConstants.ORDER_DESC)
        self.assert_(subnets is not None)
        self.assert_(len(subnets) == 2)
        self.assert_(subnets[0] is not None)
        self.assert_(subnets[0].id == subnet_ids[1])
        self.assert_(subnets[1] is not None)
        self.assert_(subnets[1].id == subnet_ids[0])

    def test_subnet_get_all_by_filters_contains(self):
        # Create Subnets
        subnet_ids = ('SN1', 'SN2', 'SN3')
        subnet_names = ('name1', 'name2', 'name3')
        subnet_net_sources = (['VS_NETWORK'], ['CLOUD_NETWORK', 'DS_NETWORK'],
                              ['DS_NETWORK'])
        for i in range(len(subnet_ids)):
            self.__create_subnet(id=subnet_ids[i], name=subnet_names[i],
                                 networkSources=subnet_net_sources[i])
        # Query with sort
        subnets = healthnmon_db_api. \
            subnet_get_all_by_filters(self.admin_context,
                                      {'networkSources':
                                      ('VS_NETWORK', 'CLOUD_NETWORK')},
                                      'id', DbConstants.ORDER_ASC)
        self.assert_(subnets is not None)
        self.assert_(len(subnets) == 2)
        self.assert_(subnets[0] is not None)
        self.assert_(subnets[0].id == subnet_ids[0])
        self.assert_(subnets[1] is not None)
        self.assert_(subnets[1].id == subnet_ids[1])

    def test_timestamp_columns(self):
        """
            Test the time stamp columns createEpoch, modifiedEpoch
            and deletedEpoch
        """
        subnet = Subnet()
        subnet.set_id('subnet-01')
        # Check for createEpoch
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.subnet_save(self.admin_context, subnet)
        epoch_after = utils.get_current_epoch_ms()
        subnet_queried = healthnmon_db_api. \
            subnet_get_by_ids(self.admin_context, [subnet.get_id()])[0]
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, subnet_queried.get_createEpoch()))
        # Check for lastModifiedEpoch
        subnet_modified = subnet_queried
        test_utils.unset_timestamp_fields(subnet_modified)
        subnet_modified.set_name('changed_name')
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.subnet_save(self.admin_context, subnet_modified)
        epoch_after = utils.get_current_epoch_ms()
        subnet_queried = healthnmon_db_api.subnet_get_by_ids(
            self.admin_context, [subnet.get_id()])[0]
        self.assert_(subnet_modified.get_createEpoch() ==
                     subnet_queried.get_createEpoch())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, subnet_queried.get_lastModifiedEpoch()))
