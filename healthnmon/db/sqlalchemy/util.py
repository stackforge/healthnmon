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


LOG = logging.getLogger(__name__)


def _create_filtered_ordered_query(session, *models, **kwargs):
    """
        Create a query on the model objects which is sorted and filtered
        Arguments:
            session - Sqlalchemy Session
            models - Model classes to be queried.
                     Filtering and ordering will be applied to the
                     first model class in list
        Keyword Arguments:
            filters - dictionary of filters to be applied
            sort_key - Column on which sorting is to be applied
            sort_dir - asc for Ascending sort direction, desc for descending
            sort direction
        Returns:
            sqlalchemy.orm.query.Query object with all the filters and ordering
    """
    # Extract kwargs
    sort_key = kwargs.pop('sort_key', None)
    sort_dir = kwargs.pop('sort_dir', None)
    filters = kwargs.pop('filters', None)
    # Create query
    query = session.query(*models)
    # Apply filters
    primary_model = models[0]
    if filters is not None:
        # Make a copy of the filters dictionary to use going forward, as we'll
        # be modifying it and we shouldn't affect the caller's use of it.
        filters = filters.copy()
        if 'changes-since' in filters:
            try:
                changes_since_val = filters.pop('changes-since')
                changes_since = long(changes_since_val)
                lastModifiedEpoch_col = getattr(primary_model,
                                                'lastModifiedEpoch')
                deletedEpoch_col = getattr(primary_model, 'deletedEpoch')
                createEpoch_col = getattr(primary_model, 'createEpoch')
                changes_since_filter = or_(
                    lastModifiedEpoch_col > changes_since,
                    deletedEpoch_col > changes_since,
                    createEpoch_col > changes_since,)
                query = query.filter(changes_since_filter)
            except ValueError:
                LOG.warn(
                    _('Invalid value for changes-since filter : '
                        + str(changes_since_val)),
                    exc_info=True)
            except AttributeError:
                LOG.warn(
                    _('Cannot apply changes-since filter to model : '
                        + str(primary_model)),
                    exc_info=True)
        if 'deleted' in filters:
            try:
                deleted_val = filters.pop('deleted')
                deleted_col = getattr(primary_model, 'deleted')
                if deleted_val == 'true':
                    query = query.filter(deleted_col == True)
                else:
                    not_deleted_filter = or_(deleted_col == False,
                                             deleted_col == None)
                    query = query.filter(not_deleted_filter)
            except AttributeError:
                LOG.warn(
                    _('Cannot apply deleted filter to model : '
                        + str(primary_model)),
                    exc_info=True)
        # Apply other filters
        filter_dict = {}
        for key in filters.keys():
            value = filters.pop(key)
            try:
                column_attr = getattr(primary_model, key)
            except AttributeError:
                LOG.warn(
                    _('Cannot apply ' + str(key) + ' filter to model : '
                        + str(primary_model)),
                    exc_info=True)
                continue
            if primary_model.get_all_members()[key].container == 1:
                # Its a list type attribute. So use contains
                if isinstance(value, (list, tuple, set, frozenset)):
                    # Use the filter column_attr contains value[0] OR
                    # column_attr contains value[1] ...
                    or_clauses = []
                    for each_value in value:
                        clause = column_attr.contains(each_value)
                        or_clauses.append(clause)
                    query = query.filter(or_(*or_clauses))
                else:
                    query = query.filter(column_attr.contains(value))
            elif isinstance(value, (list, tuple, set, frozenset)):
                # Looking for values in a list; apply to query directly
                query = query.filter(column_attr.in_(value))
            else:
                # OK, simple exact match; save for later
                filter_dict[key] = value
        if len(filter_dict) > 0:
            query = query.filter_by(**filter_dict)
    # Apply sorting
    if sort_key is not None:
        try:
            sort_col = getattr(primary_model, sort_key)
            if sort_dir == constants.DbConstants.ORDER_DESC:
                sort_fn = desc
            else:
                # Default sort asc
                sort_fn = asc
            query = query.order_by(sort_fn(sort_col))
        except AttributeError:
            LOG.warn(
                _('Cannot apply sorting as model '
                    + str(
                  primary_model) + ' do not have field ' + str(sort_key)),
                exc_info=True)
    return query


def __save_and_expunge(session, obj):
    """Save a ORM object to db and expunge the object from session
        Parameters:
        session - Sqlalchemy Session
        obj - ORM object to be saved
    """

    session.merge(obj)
    session.flush()
    session.expunge_all()


def __cleanup_session(session):
    """Clean up session
        Parameters:
        session - Sqlalchemy Session
    """

    if session is not None:
        session.flush()
        session.expunge_all()
        session.close()
