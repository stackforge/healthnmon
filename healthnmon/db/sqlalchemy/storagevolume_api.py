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


def storage_volume_save(context, storagevolume):
    """This API will create or update a StorageVolume object and its
    associations to DB. For the update to be working the VMHost object
    should have been one returned by DB API. Else it will be considered
    as a insert.
        Parameters:
        storagevolume - StorageVolume type object to be saved
        context - nova.context.RequestContext object
    """

    if storagevolume is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        epoch_time = get_current_epoch_ms()
        storagevolumes = storage_volume_get_by_ids(context,
                                                   [storagevolume.id])
        if storagevolumes:
            storagevolume.set_createEpoch(storagevolumes[0].get_createEpoch())
            storagevolume.set_lastModifiedEpoch(epoch_time)
        else:
            storagevolume.set_createEpoch(epoch_time)
        __save_and_expunge(session, storagevolume)
    except Exception:
        LOG.exception(_('error while adding/updating  StorageVolume'))
        raise
    finally:
        __cleanup_session(session)


def storage_volume_get_by_ids(context, ids):
    """This API will return a list of StorageVolume
    objects which corresponds to ids
        Parameters:
            ids - List of StorageVolume ids
            context - nova.context.RequestContext object
    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        storagevolumes = \
            session.query(
                StorageVolume).filter(
                    and_(StorageVolume.id.in_(ids),
                         or_(StorageVolume.deleted == False,
                             StorageVolume.deleted == None))).\
            options(joinedload('mountPoints')).all()
        return storagevolumes
    except Exception:
        LOG.exception(_('error while obtaining StorageVolume'))
        raise Exception('StorageVolume_get_by_id exception')
    finally:
        __cleanup_session(session)


def storage_volume_get_all(context):
    """This API will return a list of all the StorageVolume
    objects present in DB

    Parameters:
        context - nova.context.RequestContext object
    """

    session = None
    try:
        session = nova_session.get_session()
        storagevolumes = \
            session.query(
                StorageVolume).filter(
                    or_(StorageVolume.deleted == False,
                        StorageVolume.deleted == None)) \
            .options(joinedload('mountPoints')).all()
        return storagevolumes
    except Exception:
        LOG.exception(_('error while obtaining StorageVolume'))
        raise Exception('StorageVolume_get_all exception')
    finally:
        __cleanup_session(session)


def __delete_vm_storage_association(storage, context):
    vmDisks = storage.vmDisks
    if (vmDisks is not None) and (len(vmDisks) > 0):
        del vmDisks[:]


def __delete_host_storage_association(storage, context):
    try:
        hostMounts = storage.get_mountPoints()
        if len(hostMounts) > 0:
            del hostMounts[:]
    except Exception:
        LOG.exception('Error while  removing association between vmHost \
        and storageVolume')
        raise


def storage_volume_delete_by_ids(context, ids):
    """This API will delete StorageVolume objects which corresponds to ids
        Parameters:
            ids - List of VmHost ids
            context - nova.context.RequestContext object (optional parameter)

    """

    if ids is None:
        return
    session = None
    try:
        session = nova_session.get_session()
        storageVolumes = session.query(StorageVolume).\
            filter(StorageVolume.id.in_(ids)).\
            filter(or_(StorageVolume.deleted == False,
                       StorageVolume.deleted == None)).\
            options(joinedload('mountPoints')).\
            options(joinedload('vmDisks')).\
            all()
        for storageVolume in storageVolumes:
            __delete_host_storage_association(storageVolume, context)
            __delete_vm_storage_association(storageVolume, context)
            epoch_time = get_current_epoch_ms()
            storageVolume.set_deletedEpoch(epoch_time)
            storageVolume.set_deleted(True)
            __save_and_expunge(session, storageVolume)
    except Exception:
        LOG.exception(_('error while deleteing storage volume'))
        raise
    finally:
        __cleanup_session(session)


def storage_volume_get_all_by_filters(context, filters, sort_key, sort_dir):
    """
        Get all the storage volumes that match all filters
        and sorted with sort_key.
        Deleted rows will be returned by default,
        unless there's a filter that says
        otherwise
        Arguments:
            context - nova.context.RequestContext object
            filters - dictionary of filters to be applied
                      keys should be fields of StorageVolume model
                      if value is simple value = filter is applied and
                      if value is list or tuple 'IN' filter is applied
                      eg : {'size':1024, 'name':['vol1', 'vol2']}
                      will filter as
                      size = 1024 AND name in ('vol1', 'vol2')
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc
            for descending sort direction
        Returns:
            list of storage volumes that match all filters
            and sorted with sort_key
    """
    session = None
    try:
        session = nova_session.get_session()
        filtered_query = _create_filtered_ordered_query(session, StorageVolume,
                                                        filters=filters,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)
        storagevolumes = filtered_query.options(
            joinedload('mountPoints')).all()
        return storagevolumes
    except Exception:
        LOG.exception(_('Error in storage_volume_get_all_by_filters'))
        raise
    finally:
        __cleanup_session(session)
