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


def port_group_save(context, port_group):
    """This API will create or update a PortGroup object and
    its associations to DB. For the update to be working the
    port_group object should have been one returned by DB API.
    Else it will be considered as a insert.
        Parameters:
        port_group - port group object to be saved
        context - nova.context.RequestContext object (optional parameter)
    """

    if port_group is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        port_groups = port_group_get_by_ids(context, [port_group.id])
        if port_groups:
            port_group.set_createEpoch(port_groups[0].get_createEpoch())
            port_group.set_lastModifiedEpoch(epoch_time)
        else:
            port_group.set_createEpoch(epoch_time)
        __save_and_expunge(session, port_group)
    except Exception:
        LOG.exception(_('error while adding/updating  PortGroup'))
        raise
    finally:
        __cleanup_session(session)


def port_group_get_by_ids(context, ids):
    """This API will return a list of PortGroup objects
    which corresponds to ids
        Parameters:
            ids - List of port group ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        portgroups = \
            session.query(PortGroup).filter(
                and_(PortGroup.id.in_(ids),
                     or_(PortGroup.deleted == False,
                         PortGroup.deleted == None))).\
            options(joinedload('cost')).all()
        session.expunge_all()
        return portgroups
    except Exception:
        LOG.exception(_('error while obtaining PortGroup'))
        raise
    finally:
        __cleanup_session(session)


def port_group_get_all(context):
    """This API will return a list of all the PortGroup objects present in DB

    Parameters:
        context - nova.context.RequestContext object (optional parameter)
    """
    session = None
    try:
        session = nova_session.get_session()
        portgroups = \
            session.query(PortGroup).filter(
                or_(PortGroup.deleted == False,
                    PortGroup.deleted == None)).\
            options(joinedload('cost')).all()
        session.expunge_all()
        return portgroups
    except Exception:
        LOG.exception(_('error while obtaining PortGroup'))
        raise Exception('portGroup_get_all exception')
    finally:
        __cleanup_session(session)


def port_group_delete_by_ids(context, ids):
    """This API will delete port_group objects which corresponds to ids

        Parameters:
            ids - List of port group ids
            context - nova.context.RequestContext object (optional parameter)
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        portGroups = port_group_get_by_ids(context, ids)
        for portGroup in portGroups:
            epoch_time = get_current_epoch_ms()
            portGroup.set_deletedEpoch(epoch_time)
            portGroup.set_deleted(True)
            __save_and_expunge(session, portGroup)
    except Exception:
        LOG.exception(_('error while deleting the PortGroup'))
        raise
    finally:
        __cleanup_session(session)
