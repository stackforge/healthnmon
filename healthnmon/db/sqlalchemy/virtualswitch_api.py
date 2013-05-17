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
from healthnmon.db.sqlalchemy import portgroup_api


LOG = logging.getLogger(__name__)


def virtual_switch_save(context, virtual_switch):
    """This API will create or update a VirtualSwitch object
    and its associations to DB. For the update to be working
    the virtual_switch object should have been one returned by DB API.
    Else it will be considered as a insert.
        Parameters:
        virtual_switch - network type object to be saved
        context - nova.context.RequestContext object (optional parameter)
    """
    if virtual_switch is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        virtual_switches = virtual_switch_get_by_ids(context,
                                                     [virtual_switch.id])
        if virtual_switches:
            # Add the extracted createEpcoh and the new epoch to
            # lastModifiedEpoch to the added portGroups
            pGroupDict = {}
            for virtualswitch in virtual_switches:
                pgs = virtualswitch.get_portGroups()
                for pg in pgs:
                    pGroupDict[pg.get_id()] = pg.get_createEpoch()
            virtual_switch.set_createEpoch(
                virtual_switches[0].get_createEpoch())
            virtual_switch.set_lastModifiedEpoch(epoch_time)
            portGroups = virtual_switch.get_portGroups()
            for portGroup in portGroups:
                portId = portGroup.get_id()
                if portId in pGroupDict:
                    portGroup.set_createEpoch(pGroupDict[portId])
                    portGroup.set_lastModifiedEpoch(epoch_time)
                else:
                    portGroup.set_createEpoch(epoch_time)
        else:
            virtual_switch.set_createEpoch(epoch_time)
            for portGroup in virtual_switch.get_portGroups():
                portGroup.set_createEpoch(epoch_time)

        __save_and_expunge(session, virtual_switch)
    except Exception:
        LOG.exception(_('error while adding/updating  VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


def virtual_switch_get_by_ids(context, ids):
    """This API will return a list of virtual switch objects
    which corresponds to ids

        Parameters:
            ids - List of virtual switch ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        virtualswitches = \
            session.query(VirtualSwitch).filter(
                and_(VirtualSwitch.id.in_(ids),
                     or_(VirtualSwitch.deleted == False,
                         VirtualSwitch.deleted == None))).\
            options(joinedload('cost')).\
            options(joinedload_all('portGroups.cost')).\
            options(joinedload('networks')).\
            options(joinedload('subnets')).all()
        return virtualswitches
    except Exception:
        LOG.exception(_('error while obtaining VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


def virtual_switch_get_all(context):
    """This API will return a list of all the
    virtual switch objects present in Db
    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """

    session = None
    try:
        session = nova_session.get_session()
        virtualswitches = \
            session.query(VirtualSwitch).filter(
                or_(VirtualSwitch.deleted == False,
                    VirtualSwitch.deleted == None)).\
            options(joinedload('cost')).\
            options(joinedload_all('portGroups.cost')).\
            options(joinedload('networks')).\
            options(joinedload('subnets')).all()

        return virtualswitches
    except Exception:
        LOG.exception(_('error while obtaining VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


def virtual_switch_delete_by_ids(context, ids):
    """This API will delete virtual switch objects which corresponds to ids
        Parameters:
            ids - List of virtual switch ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        vSwitches = virtual_switch_get_by_ids(context, ids)
        portGroupIds = \
            session.query(
                PortGroup.id).filter(and_(PortGroup.virtualSwitchId.in_(ids),
                                     or_(PortGroup.deleted == False,
                                         PortGroup.deleted == None))).all()
        pgIds = []
        for portGroupId in portGroupIds:
            pg_tuple = portGroupId[0]
            pgIds.append(pg_tuple)
        portgroup_api.port_group_delete_by_ids(context, pgIds)
        for vSwitch in vSwitches:
            epoch_time = get_current_epoch_ms()
            vSwitch.set_deletedEpoch(epoch_time)
            vSwitch.set_deleted(True)
            __save_and_expunge(session, vSwitch)
    except Exception:
        LOG.exception(_('error while deleting the VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)


def _load_deleted_switches(session, vswitches):
    for vs in vswitches:
            vs_id = vs.get_id()
            deleted_vs_pg = session.query(PortGroup).\
                filter(and_(PortGroup.deleted == True,
                            PortGroup.virtualSwitchId == vs_id)).\
                options(joinedload('cost')).all()
            for pg in deleted_vs_pg:
                vs.add_portGroups(pg)


def virtual_switch_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the virtual_switch that match all filters and
        sorted with sort_key.
        Deleted rows will be returned by default,
        unless there's a filter that says
        otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of VirtualSwitch model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'switchType':'abc', 'name':['n1', 'n2']}
                      will filter as
                      switchType = 'abc' AND name in ('n1', 'n2')
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for
            descending sort direction
        Returns:
            list of virtual_switch that match all filters and
            sorted with sort_key
    """
    session = None
    try:
        session = nova_session.get_session()
        filtered_query = _create_filtered_ordered_query(session, VirtualSwitch,
                                                        filters=filters,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)
        virtualswitches = filtered_query.options(
            joinedload_all('portGroups.cost')).\
            options(joinedload('cost')).\
            options(joinedload('networks')).\
            options(joinedload('subnets')).all()

        if filters is not None and 'deleted' in filters:
            vs_filters = filters.copy()
            deleted_val = vs_filters.pop('deleted')
            if deleted_val and deleted_val == 'true':
                _load_deleted_switches(session, virtualswitches)
        return virtualswitches
    except Exception:
        LOG.exception(_('Error while obtaining VirtualSwitch'))
        raise
    finally:
        __cleanup_session(session)
