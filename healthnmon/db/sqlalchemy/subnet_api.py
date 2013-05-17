# vim: tabstop=4 shiftwidth=4 softtabstop=4

#          (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
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


from sqlalchemy.orm import joinedload, joinedload_all
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    Vm, StorageVolume, HostMountPoint, VirtualSwitch, PortGroup, \
    Subnet
from healthnmon.db.sqlalchemy.mapper import VirtualSwitchSubnetIds
from nova.openstack.common.db.sqlalchemy import session as nova_session
from nova.db.sqlalchemy import api as context_api
from healthnmon import log as logging
from healthnmon import constants
from healthnmon.utils import get_current_epoch_ms
from healthnmon.db.sqlalchemy.util import _create_filtered_ordered_query, \
    __save_and_expunge, __cleanup_session


LOG = logging.getLogger(__name__)


def _get_deleted_obj(inv_obj_id_list, db_obj_list, epoch_time):
    to_be_deleted_obj = []
    for db_obj in db_obj_list:
        if db_obj.get_id() not in inv_obj_id_list:
            db_obj.set_deletedEpoch(epoch_time)
            db_obj.set_deleted(True)
            to_be_deleted_obj.append(db_obj)
    return to_be_deleted_obj


def subnet_save(context, subnet):
    """This API will create or update a Subnet object and
    its associations to DB. For the update to be working the
    subnet object should have been one returned by DB API.
    Else it will be considered as a insert.
        Parameters:
        subnet - port group object to be saved
        context - nova.context.RequestContext object (optional parameter)
    """

    if subnet is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        subnets = subnet_get_by_ids(context, [subnet.id])
        if subnets:
            subnet.set_createEpoch(subnets[0].get_createEpoch())
            subnet.set_lastModifiedEpoch(epoch_time)
            # set for ipaddress
            ipaddress_existing = subnets[0].get_usedIpAddresses()
            ipadd_dict = {}
            for ipaddress in ipaddress_existing:
                ipadd_dict[ipaddress.get_id()] = ipaddress.get_createEpoch()
            usedipaddress = subnet.get_usedIpAddresses()
            usedip_id_list = []
            for usedip in usedipaddress:
                usedip_id_list.append(usedip.get_id())
                if usedip.get_id() in ipadd_dict:
                    usedip.set_createEpoch(ipadd_dict[usedip.get_id()])
                    usedip.set_lastModifiedEpoch(epoch_time)
                else:
                    usedip.set_createEpoch(epoch_time)

            # set for ipaddressRange
            ipaddress_range_existing = subnets[0].get_ipAddressRanges()
            ipaddr_dict = {}
            for ipaddress_r in ipaddress_range_existing:
                ipaddr_dict[ipaddress_r.get_id()] = ipaddress_r.\
                    get_createEpoch()
            ipaddress_range = subnet.get_ipAddressRanges()
            ip_range_id_list = []
            for ip_range in ipaddress_range:
                ip_range_id_list.append(ip_range.get_id())
                if ip_range.get_id() in ipaddr_dict:
                    ip_range.set_createEpoch(ipaddr_dict[ip_range.get_id()])
                    ip_range.set_lastModifiedEpoch(epoch_time)
                else:
                    ip_range.set_createEpoch(epoch_time)
            # if the any ipaddres is not in new subnet and present
            # in db, then update the deleteEpoch and mark as deleted

            # Get the deleted ipAddresses and ip-Ranges and set the
            # deleted flag and deletedEpoch value."
            deleted_ipAddress = _get_deleted_obj(
                usedip_id_list, ipaddress_existing, epoch_time)
            deleted_ipRanges = _get_deleted_obj(
                ip_range_id_list, ipaddress_range_existing, epoch_time)
            for deleted_ip in deleted_ipAddress:
                subnet.add_usedIpAddresses(deleted_ip)
            for deleted_ipRange in deleted_ipRanges:
                subnet.add_ipAddressRanges(deleted_ipRange)
        else:
            subnet.set_createEpoch(epoch_time)
            for ipaddr in subnet.get_usedIpAddresses():
                ipaddr.set_createEpoch(epoch_time)
            for ipadd_r in subnet.get_ipAddressRanges():
                ipadd_r.set_createEpoch(epoch_time)

        __save_and_expunge(session, subnet)
    except Exception:
        LOG.exception(_('error while adding/updating  Subnet'))
        raise
    finally:
        __cleanup_session(session)


def subnet_get_by_ids(context, ids):
    """This API will return a list of subnet objects which corresponds to ids

        Parameters:
            ids - List of subnet ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        subnets = session.query(Subnet).filter(
            and_(Subnet.id.in_(ids),
                 or_(Subnet.deleted == False,
                     Subnet.deleted == None))).\
            options(joinedload_all('groupIdTypes.networkType')).\
            options(joinedload('resourceTags')).\
            options(joinedload_all('ipAddressRanges.startAddress')).\
            options(joinedload_all('ipAddressRanges.endAddress')).\
            options(joinedload('usedIpAddresses')).\
            options(joinedload('parents')).\
            options(joinedload('networkSrc')).\
            options(joinedload('dnsServer')).\
            options(joinedload('dnsSuffixes')).\
            options(joinedload('defaultGateway')).\
            options(joinedload('winsServer')).\
            options(joinedload('ntpDateServer')).\
            options(joinedload('deploymentService')).\
            options(joinedload('childs')).\
            options(joinedload('redundancyPeer')).all()
        return subnets
    except Exception:
        LOG.exception(_('error while obtaining Subnets'))
        raise
    finally:
        __cleanup_session(session)


def subnet_get_all(context):
    """This API will return a list of all the Subnet objects present in DB
    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """
    session = None
    try:
        session = nova_session.get_session()
        subnets = session.query(Subnet).filter(
            or_(Subnet.deleted == False,
                Subnet.deleted == None)).\
            options(joinedload_all('groupIdTypes.networkType')).\
            options(joinedload('resourceTags')).\
            options(joinedload_all('ipAddressRanges.startAddress')).\
            options(joinedload_all('ipAddressRanges.endAddress')).\
            options(joinedload('usedIpAddresses')).\
            options(joinedload('parents')).\
            options(joinedload('networkSrc')).\
            options(joinedload('dnsServer')).\
            options(joinedload('dnsSuffixes')).\
            options(joinedload('defaultGateway')).\
            options(joinedload('winsServer')).\
            options(joinedload('ntpDateServer')).\
            options(joinedload('deploymentService')).\
            options(joinedload('childs')).\
            options(joinedload('redundancyPeer')).all()
        return subnets
    except Exception:
        LOG.exception(_('error while obtaining Subnets'))
        raise
    finally:
        __cleanup_session(session)


def __delete_vSwitch_subnet_association(session, subnetId):
    vSwitches = session.query(
        VirtualSwitch, VirtualSwitchSubnetIds).filter(
            and_(VirtualSwitchSubnetIds.subnetId == subnetId,
                 or_(VirtualSwitch.deleted == False,
                     VirtualSwitch.deleted == None))).\
        options(joinedload_all('subnets')).all()
    if len(vSwitches) > 0:
        subnetList = []
        for vSwitchType in vSwitches:
            vSwitch = vSwitchType[0]
            subnets = vSwitch.get_subnetIds()
            for subnet in subnets:
                if not subnet == subnetId:
                    subnetList.append(subnet)
            vSwitch.set_subnetIds([])
            __save_and_expunge(session, vSwitch)
            if len(subnetList) > 0:
                vSwitch.set_subnetIds(subnetList)
            __save_and_expunge(session, vSwitch)


def subnet_delete_by_ids(context, ids):
    """This API will delete Subnets objects which corresponds to ids
        Parameters:
            ids - List of subnets ids
            context - nova.context.RequestContext object (optional parameter)

    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        subnets = subnet_get_by_ids(context, ids)
        epoch_time = get_current_epoch_ms()
        for subnet in subnets:
            __delete_vSwitch_subnet_association(session, subnet.id)
            subnet.set_deletedEpoch(epoch_time)
            subnet.set_deleted(True)
            usedIpAddresses = subnet.get_usedIpAddresses()
            for usedIp in usedIpAddresses:
                usedIp.set_deletedEpoch(epoch_time)
                usedIp.set_deleted(True)
            for ip_range in subnet.get_ipAddressRanges():
                ip_range.set_deletedEpoch(epoch_time)
                ip_range.set_deleted(True)
            __save_and_expunge(session, subnet)
    except Exception:
        LOG.exception(_('error while obtaining Subnet'))
        raise
    finally:
        __cleanup_session(session)


def subnet_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the subnet that match all filters and sorted with sort_key.
        Deleted rows will be returned by default,
        unless there's a filter that says
        otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of Subnet model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'isPublic':True, 'name':['n1', 'n2']}
                      will filter as
                      isPublic = True AND name in ('n1', 'n2')
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction,
            desc for descending sort direction
        Returns:
            list of subnet that match all filters and sorted with sort_key
    """
    session = None
    try:
        session = nova_session.get_session()
        filtered_query = _create_filtered_ordered_query(session,
                                                        Subnet,
                                                        filters=filters,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)
        subnets = filtered_query.\
            options(joinedload_all('groupIdTypes.networkType')).\
            options(joinedload('resourceTags')).\
            options(joinedload_all('ipAddressRanges.startAddress')).\
            options(joinedload_all('ipAddressRanges.endAddress')).\
            options(joinedload('usedIpAddresses')).\
            options(joinedload('parents')).\
            options(joinedload('networkSrc')).\
            options(joinedload('dnsServer')).\
            options(joinedload('dnsSuffixes')).\
            options(joinedload('defaultGateway')).\
            options(joinedload('winsServer')).\
            options(joinedload('ntpDateServer')).\
            options(joinedload('deploymentService')).\
            options(joinedload('childs')).\
            options(joinedload('redundancyPeer')).all()
        return subnets
    except Exception:
        LOG.exception(_('Error while obtaining Subnets'))
        raise
    finally:
        __cleanup_session(session)
