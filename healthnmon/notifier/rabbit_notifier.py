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

""" Healthnmon notification driver which sends message to rabbitmq
"""

from nova.openstack.common import cfg
from nova.openstack.common import rpc
from nova import context as req_context

CONF = cfg.CONF


def notify(context, message):
    """Sends a notification to the RabbitMQ"""
    if not context:
        context = req_context.get_admin_context()

    priority = message.get('priority',
                           CONF.healthnmon_default_notification_level)
    priority = priority.lower()

    # Construct topic name
# As the below code use to create multiple queues, it is removed
    topic_parts = []
    topic_parts.append('healthnmon_notification')
    topic_parts.append(priority)
    event_type = message.get('event_type', None)
    if event_type is not None:
        topic_parts.append(event_type)
        payload = message.get('payload', None)
        if payload is not None:
            entity_id = payload.get('entity_id', None)
            if entity_id is not None:
                topic_parts.append(entity_id)
    topic = '.'.join(topic_parts)

    rpc.notify(context, "healthnmon_notification", message)
