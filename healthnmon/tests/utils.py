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
Common methods for unit tests
"""


def is_timestamp_between(before, after, actual):
    """
        Check if the actual time stamp is in between
        before and after time stamps
    """
    return ((actual is not None) and (actual >= before) and (actual <= after))


def unset_timestamp_fields(model_obj):
    """
        Set the time stamp fields and deleted field
        of a resource model object and its contained objects
    """
    if model_obj is None:
        return
    if isinstance(model_obj, (list, tuple, set)):
        for obj in model_obj:
            unset_timestamp_fields(obj)
    if hasattr(model_obj, 'lastModifiedEpoch'):
        setattr(model_obj, 'lastModifiedEpoch', None)
    if hasattr(model_obj, 'deletedEpoch'):
        setattr(model_obj, 'deletedEpoch', None)
    if hasattr(model_obj, 'createEpoch'):
        setattr(model_obj, 'createEpoch', None)
    if hasattr(model_obj, 'deleted'):
        setattr(model_obj, 'deleted', None)
    if model_obj.__class__.__module__.startswith(
            'healthnmon.resourcemodel.healthnmonResourceModel'):
        for member_key in model_obj.get_all_members().keys():
            member = getattr(model_obj, member_key)
            unset_timestamp_fields(member)
    return
