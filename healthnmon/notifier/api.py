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

""" Healthnmon notifier api
Implements the healthnmon notifier API
"""

import uuid

from oslo.config import cfg
from nova.openstack.common import timeutils, jsonutils, importutils
from healthnmon import log as logging
import time
from healthnmon.constants import Constants

LOG = logging.getLogger('healthnmon.notifier.api')

CONF = cfg.CONF

WARN = 'WARN'
INFO = 'INFO'
ERROR = 'ERROR'
CRITICAL = 'CRITICAL'
DEBUG = 'DEBUG'

priorities = (DEBUG, WARN, INFO, ERROR, CRITICAL)

drivers = None


class BadPriorityException(Exception):

    pass


def notify(context,
           publisher_id,
           event_type,
           priority,
           payload,
           ):
    """
    Sends a notification using the specified driver

    Notify parameters:

    publisher_id - the source of the message. Cannot be none.
    event_type - the literal type of event (ex. LifeCycle.Vm.Created)
    priority - patterned after the enumeration of Python logging levels in
               the set (DEBUG, WARN, INFO, ERROR, CRITICAL)
    payload - A python dictionary of attributes

    Outgoing message format includes the above parameters, and appends the
    following:

    message_id - a UUID representing the id for this notification
    timestamp - the GMT timestamp the notification was sent at

    The composite message will be constructed as a dictionary of the above
    attributes, which will then be sent via the transport mechanism defined
    by the driver.

    Message example:

    {'message_id': str(uuid.uuid4()),
     'publisher_id': 'compute.host1',
     'timestamp': utils.utcnow(),
     'priority': 'WARN',
     'event_type': 'LifeCycle.Vm.Created',
     'payload': {'entity_id': 'XXXX', ... }}

    """

    if priority not in priorities:
        raise BadPriorityException(_('%s not in valid priorities'
                                   % priority))

    # Ensure everything is JSON serializable.

    payload = jsonutils.to_primitive(payload, convert_instances=True)

    msg = dict(
        message_id=str(uuid.uuid4()),
        publisher_id=publisher_id,
        event_type=event_type,
        priority=priority,
        payload=payload,
        timestamp=time.strftime(
            Constants.DATE_TIME_FORMAT, timeutils.utcnow().timetuple()),
    )
    for driver in _get_drivers():
        try:
            driver.notify(context, msg)
        except Exception, e:
            LOG.exception(_("Problem '%(e)s' attempting to send to \
            healthnmon notification driver %(driver)s."
                            % locals()))


def _get_drivers():
    """Instantiates and returns drivers based on the flag values."""
    global drivers
    if not drivers:
        drivers = []
        for notification_driver in CONF.healthnmon_notification_drivers:
            drivers.append(importutils.import_module(notification_driver))
    return drivers
