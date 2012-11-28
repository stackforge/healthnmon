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

"""Event types module
    Module declaring and handling different event types supported by healthnmon
"""

import healthnmon.notifier.api as notifier_api


class BadEventTypeException(Exception):

    pass


class EventMetaData(object):

    """Attributes specific to type of event

        Attributes:
            event_type_name - Name of this event type meta data like VmHost.Connected, VmHost.Disconnected etc
            event_category - Category of the event like "LifeCycle", "Threshold" etc
            short_desc_template - A template for short description of the event
            long_desc_template - A template for long description of the event
            priority - Priority of the event (DEBUG, INFO, WARN, ERROR, CRITICAL)
    """

    def __init__(
        self,
        event_type_name,
        event_category,
        short_desc_template,
        long_desc_template,
        priority,
    ):
        self.event_type_name = event_type_name
        self.event_category = event_category
        self.short_desc_template = short_desc_template
        self.long_desc_template = long_desc_template
        self.priority = priority

    def __get_formatted_string(
        self,
        template_str,
        obj,
        **kwargs
    ):
        obj_members = obj.get_all_members()
        placeholder_values = {}

        # kwargs will have priority over object's attributes

        placeholder_values.update(kwargs)
        for obj_mem in obj_members.keys():
            obj_mem_val = getattr(obj, obj_mem)
            if not obj_mem in kwargs and isPrimitive(obj_mem_val):
            #if not kwargs.has_key(obj_mem) and isPrimitive(obj_mem_val):
                placeholder_values[obj_mem] = str(obj_mem_val)
        formatted_str = template_str % placeholder_values
        return formatted_str

    def get_short_desc(self, obj, **kwargs):
        """Get Short description text replaced with place holder values
        If template has placeholder keys which are not in the obj's attribute list
        then those should be passed as keyword arguments

        Parameters:
            obj - Resource model object to which this event is associated.
                  The template placeholders will be replaced with object's attribute values.
        """

        return self.__get_formatted_string(self.short_desc_template,
                                           obj, **kwargs)

    def get_long_desc(self, obj, **kwargs):
        """Get long description text replaced with place holder values
        If template has placeholder keys which are not in the obj's attribute list
        then those should be passed as keyword arguments

        Parameters:
            obj - Resource model object to which this event is associated.
                  The template placeholders will be replaced with object's attribute values.
        """

        return self.__get_formatted_string(self.long_desc_template,
                                           obj, **kwargs)

    def get_topic_name(self, objuuid):
        """Get the topic name to be used for a event related to this metadata
        Topic name is of format healthnmon_notification.<PRIORITY>.<Category>.<<ObjectType>.<EventName>>.<UUID>

        Parameters:
            objuuid - UUID of the Resource model object to which this event is associated.
        """

        return '.'.join(['healthnmon_notification', self.priority,
                        self.event_category, self.event_type_name,
                        objuuid])

    def get_event_fully_qal_name(self):
        """Get the fully qualified name of this event type
        Fully qualified name is <Category>.<<ObjectType>.<EventName>>
        """

        return '.'.join([self.event_category, self.event_type_name])


# End class EventMetaData

def isPrimitive(obj):
    if obj is None:
        return True
    primitives = (
        bool,
        int,
        long,
        float,
        str,
        unicode,
    )
    is_primitive = isinstance(obj, primitives)
    return is_primitive


#
# Event categories
#

EVENT_CATEGORY_LIFECYCLE = 'LifeCycle'
EVENT_CATEGORY_THRESHOLD = 'Threshold'

#
# Declare event type names and EventMetaData objects for those events
#

# VmHost Events

EVENT_TYPE_HOST_CONNECTED = 'VmHost.Connected'
EVENT_TYPE_HOST_DISCONNECTED = 'VmHost.Disconnected'
EVENT_TYPE_HOST_ADDED = 'VmHost.Added'
EVENT_TYPE_HOST_UPDATED = 'VmHost.Updated'
EVENT_TYPE_HOST_REMOVED = 'VmHost.Removed'

# Vm Events

EVENT_TYPE_VM_STARTED = 'Vm.StateChanged.Started'
EVENT_TYPE_VM_STOPPED = 'Vm.StateChanged.Stopped'
EVENT_TYPE_VM_SUSPENDED = 'Vm.StateChanged.Suspended'
EVENT_TYPE_VM_RESUMED = 'Vm.StateChanged.Resumed'
EVENT_TYPE_VM_SHUTDOWN = 'Vm.StateChanged.Shutdown'
EVENT_TYPE_VM_CREATED = 'Vm.Created'
EVENT_TYPE_VM_DELETED = 'Vm.Deleted'
EVENT_TYPE_VM_RECONFIGURED = 'Vm.Reconfigured'

# Storage Events

EVENT_TYPE_STORAGE_ADDED = 'StorageVolume.Added'
EVENT_TYPE_STORAGE_DELETED = 'StorageVolume.Deleted'
EVENT_TYPE_STORAGE_ENABLED = 'StorageVolume.Enabled'
EVENT_TYPE_STORAGE_DISABLED = 'StorageVolume.Disabled'

# Network Events

EVENT_TYPE_NETWORK_ADDED = 'Network.Added'
EVENT_TYPE_NETWORK_DELETED = 'Network.Deleted'
EVENT_TYPE_NETWORK_ENABLED = 'Network.Enabled'
EVENT_TYPE_NETWORK_DISABLED = 'Network.Disabled'
EVENT_TYPE_PORTGROUP_ADDED = 'PortGroup.Added'
EVENT_TYPE_PORTGROUP_DELETED = 'PortGroup.Deleted'
EVENT_TYPE_PORTGROUP_RECONFIGURED = 'PortGroup.Reconfigured'

# Compute Events

EVENT_TYPE_RUN_INSTANCE_CREATE = 'run_instance.start'

eventMetadataDict = {}
eventMetadataDict[EVENT_TYPE_HOST_CONNECTED] = \
    EventMetaData(EVENT_TYPE_HOST_CONNECTED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM Host %(name)s connected'),
                  _('Healthnmon service can successfully connect to VM Host %(name)s'
                    ), notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_HOST_DISCONNECTED] = \
    EventMetaData(EVENT_TYPE_HOST_DISCONNECTED,
                  EVENT_CATEGORY_LIFECYCLE,
                  _('VM Host %(name)s disconnected'),
                  _('Healthnmon service lost connection to the host %(name)s'
                    ), notifier_api.CRITICAL)
eventMetadataDict[EVENT_TYPE_HOST_ADDED] = \
    EventMetaData(EVENT_TYPE_HOST_ADDED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM Host %(name)s added'),
                  _('A new VM Host %(name)s is added for healthnmon service monitoring'
                    ), notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_HOST_UPDATED] = \
    EventMetaData(EVENT_TYPE_HOST_UPDATED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM Host %(name)s updated'),
                  _('VM Host %(name)s has been updated'
                    ), notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_HOST_REMOVED] = \
    EventMetaData(EVENT_TYPE_HOST_REMOVED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM Host %(name)s removed'),
                  _('VM Host %(name)s is removed from healthnmon service'
                    ), notifier_api.INFO)

eventMetadataDict[EVENT_TYPE_VM_STARTED] = \
    EventMetaData(EVENT_TYPE_VM_STARTED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM %(name)s started'),
                  _('VM %(name)s started successfully'),
                  notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_VM_STOPPED] = \
    EventMetaData(EVENT_TYPE_VM_STOPPED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM %(name)s stopped'),
                  _('VM %(name)s has been stopped'), notifier_api.WARN)
eventMetadataDict[EVENT_TYPE_VM_SUSPENDED] = \
    EventMetaData(EVENT_TYPE_VM_SUSPENDED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM %(name)s suspended'),
                  _('VM %(name)s has been suspended'),
                  notifier_api.WARN)
eventMetadataDict[EVENT_TYPE_VM_RESUMED] = \
    EventMetaData(EVENT_TYPE_VM_RESUMED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM %(name)s resumed'),
                  _('VM %(name)s has been resumed'), notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_VM_SHUTDOWN] = \
    EventMetaData(EVENT_TYPE_VM_SHUTDOWN, EVENT_CATEGORY_LIFECYCLE,
                  _('VM %(name)s shutdown'),
                  _('VM %(name)s has been shutdown'), notifier_api.WARN)
eventMetadataDict[EVENT_TYPE_VM_CREATED] = \
    EventMetaData(EVENT_TYPE_VM_CREATED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM %(name)s created'),
                  _('A new VM %(name)s created successfully'),
                  notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_VM_DELETED] = \
    EventMetaData(EVENT_TYPE_VM_DELETED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM %(name)s deleted'), _('VM %(name)s deleted'),
                  notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_VM_RECONFIGURED] = \
    EventMetaData(EVENT_TYPE_VM_RECONFIGURED, EVENT_CATEGORY_LIFECYCLE,
                  _('VM %(name)s reconfigured'),
                  _('VM %(name)s reconfigured. Changed attributes are %(changed_attributes)s'
                    ), notifier_api.INFO)

eventMetadataDict[EVENT_TYPE_STORAGE_ADDED] = \
    EventMetaData(EVENT_TYPE_STORAGE_ADDED, EVENT_CATEGORY_LIFECYCLE,
                  _('Storage volume %(name)s added'),
                  _('A new Storage volume %(name)s added'),
                  notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_STORAGE_DELETED] = \
    EventMetaData(EVENT_TYPE_STORAGE_DELETED, EVENT_CATEGORY_LIFECYCLE,
                  _('Storage volume %(name)s deleted'),
                  _('Storage volume %(name)s deleted'),
                  notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_STORAGE_ENABLED] = \
    EventMetaData(EVENT_TYPE_STORAGE_ENABLED, EVENT_CATEGORY_LIFECYCLE,
                  _('Storage volume %(name)s enabled'),
                  _('Storage volume %(name)s enabled'),
                  notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_STORAGE_DISABLED] = \
    EventMetaData(EVENT_TYPE_STORAGE_DISABLED,
                  EVENT_CATEGORY_LIFECYCLE,
                  _('Storage volume %(name)s disabled'),
                  _('Storage volume %(name)s disabled'),
                  notifier_api.WARN)

eventMetadataDict[EVENT_TYPE_NETWORK_ADDED] = \
    EventMetaData(EVENT_TYPE_NETWORK_ADDED, EVENT_CATEGORY_LIFECYCLE,
                  _('Host network %(name)s added'),
                  _('A new host network %(name)s added to host %(host_id)s'
                    ), notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_NETWORK_DELETED] = \
    EventMetaData(EVENT_TYPE_NETWORK_DELETED, EVENT_CATEGORY_LIFECYCLE,
                  _('Host network %(name)s deleted'),
                  _('Network %(name)s deleted from host %(host_id)s '),
                  notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_NETWORK_ENABLED] = \
    EventMetaData(EVENT_TYPE_NETWORK_ENABLED, EVENT_CATEGORY_LIFECYCLE,
                  _('Host network %(name)s enabled'),
                  _('Network %(name)s started on host %(host_id)s '),
                  notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_NETWORK_DISABLED] = \
    EventMetaData(EVENT_TYPE_NETWORK_DISABLED,
                  EVENT_CATEGORY_LIFECYCLE,
                  _('Host network %(name)s disabled'),
                  _('Network %(name)s disabled on host %(host_id)s '),
                  notifier_api.WARN)
eventMetadataDict[EVENT_TYPE_PORTGROUP_ADDED] = \
    EventMetaData(EVENT_TYPE_PORTGROUP_ADDED, EVENT_CATEGORY_LIFECYCLE,
                  _('Port group %(name)s added'),
                  _('Port group %(name)s added to virtual switch %(virtualSwitchId)s'
                    ), notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_PORTGROUP_DELETED] = \
    EventMetaData(EVENT_TYPE_PORTGROUP_DELETED,
                  EVENT_CATEGORY_LIFECYCLE,
                  _('Port group %(name)s deleted'),
                  _('Port group %(name)s removed from virtual switch %(virtualSwitchId)s'
                    ), notifier_api.INFO)
eventMetadataDict[EVENT_TYPE_PORTGROUP_RECONFIGURED] = \
    EventMetaData(EVENT_TYPE_PORTGROUP_RECONFIGURED,
                  EVENT_CATEGORY_LIFECYCLE,
                  _('Port group %(name)s reconfigured'),
                  _(' Port group %(name)s attached to virtual switch %(virtualSwitchId)s reconfigured. Changed attributes are %(changed_attributes)s'
                    ), notifier_api.INFO)


def get_EventMetaData(event_type):
    """Get the EventMetaData object for a EVENT_TYPE string
    This API is used by the different healthnmon modules which need to generate event.

            Parameters:
                event_type - One of the event types like EVENT_TYPE_HOST_CONNECTED, EVENT_TYPE_HOST_DISCONNECTED etc
            Returns:
                EventMetaData for event_type string
            Raises:
                BadEventTypeException if event_type string is not a supported one
    """

    if not event_type in eventMetadataDict:
        raise BadEventTypeException(_('%s not in valid event types'
                                    % event_type))
    return eventMetadataDict[event_type]
