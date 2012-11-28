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
ResourceModelDiff - Handles comparing two resource model objects
and provides dictionary of add, update and delete attributes
"""

from healthnmon import log as logging

logging = logging.getLogger('healthnmon.resourcemodeldiff')


class ResourceModelDiff(object):

    """
    ResourceModelDIff - Handles comparing two resource model objects
    and provides dictionary of add, update and delete attributes
    """

    def __init__(self, old_resource_model=None,
                 new_resource_model=None):
        self.old_modelobj = old_resource_model
        self.new_modelobj = new_resource_model

    def _collate_results(self, result):
        """Method to collate the results"""

        out_result = {}
        for change_type in result:
            temp_dict = {}
            for key in result[change_type]:
                logging.debug(_('change_type = %s') % change_type)
                temp_dict[key] = result[change_type][key]
            if len(temp_dict) > 0:
                out_result[change_type] = temp_dict

        return out_result

    def _diff_objects(self, old_obj, new_obj):
        """Unify decision making on the leaf node level."""

        res = None
        if old_obj.__class__.__module__.startswith('healthnmon.resourcemodel.healthnmonResourceModel'
                                                   ):
            res_dict = self.diff_resourcemodel(old_obj, new_obj)
            if len(res_dict) > 0:
                res = res_dict
        elif isinstance(old_obj, dict):

        # We want to go through the tree post-order

            res_dict = self._diff_dicts(old_obj, new_obj)
            if len(res_dict) > 0:
                res = res_dict
        # Now we are on the same level
        # different types, new value is new
        elif type(old_obj) != type(new_obj):
            # In case we have the unicode type for old_obj from db
            # and string type in the newly created object,
            # both having the same values
            if ((type(old_obj) in [str, unicode]) and
                    (type(new_obj) in [str, unicode])):
                primitive_diff = self._diff_primitives(old_obj, new_obj)
                if primitive_diff is not None:
                    res = primitive_diff
            # In all the other cases, if type changes return the new obj.
            else:
                res = new_obj
        elif isinstance(old_obj, list):

        # recursive arrays
        # we can be sure now, that both new and old are
        # of the same type

            res_list = self._diff_lists(old_obj, new_obj)
            if len(res_list) > 0:
                res = res_list
        else:

        # the only thing remaining are scalars

            primitive_diff = self._diff_primitives(old_obj, new_obj)
            if primitive_diff is not None:
                res = primitive_diff

        return res

    def _diff_primitives(
        self,
        old,
        new,
        name=None,
    ):
        """
        Method to check diff of primitive types
        """

        if old != new:
            return new
        else:
            return None

    def _diff_lists(self, old_list, new_list):
        """
        Method to check diff of list types

        As we are processing two ResourceModel objects both the lists should be of same type
        """

        result = {'_add': {}, '_delete': {}, '_update': {}}

        if len(old_list) > 0 and hasattr(old_list[0], 'id'):
            addlistindex = 0
            removelistindex = 0
            updatelistindex = 0
            for old_idx in range(len(old_list)):
                obj_not_in_new_list = True
                for new_idx in range(len(new_list)):
                    if getattr(old_list[old_idx], 'id') \
                            == getattr(new_list[new_idx], 'id'):
                        obj_not_in_new_list = False
                        res = self._diff_objects(old_list[old_idx],
                                                 new_list[new_idx])
                        if res is not None:
                            result['_update'
                                   ][getattr(new_list[new_idx], 'id'
                                             )] = res
                            updatelistindex += 1
                        break

                if obj_not_in_new_list:
                    result['_delete'][getattr(old_list[old_idx], 'id'
                                              )] = old_list[old_idx]
                    removelistindex += 1

            for new_idx in range(len(new_list)):
                obj_not_in_old_list = True
                for old_idx in range(len(old_list)):
                    if getattr(old_list[old_idx], 'id') \
                            == getattr(new_list[new_idx], 'id'):
                        obj_not_in_old_list = False
                        break

                if obj_not_in_old_list:
                    result['_add'][getattr(new_list[new_idx], 'id')] = \
                        new_list[new_idx]
                    addlistindex += 1
        else:
            shorterlistlen = min(len(old_list), len(new_list))
            for idx in range(shorterlistlen):
                res = self._diff_objects(old_list[idx], new_list[idx])
                if res is not None:
                    result['_update'][idx] = res

            # the rest of the larger array

            if shorterlistlen == len(old_list):
                for idx in range(shorterlistlen, len(new_list)):
                    result['_add'][idx] = new_list[idx]
            else:
                for idx in range(shorterlistlen, len(old_list)):
                    result['_delete'][idx] = old_list[idx]

        return self._collate_results(result)

    def _diff_dicts(self, old_obj=None, new_obj=None):
        """
        Method to check diff of dictionary types

        As we are processing two ResourceModel objects both the dictionaries should be of same type
        """

        old_keys = set()
        new_keys = set()
        if old_obj and len(old_obj) > 0:
            old_keys = set(old_obj.keys())
        if new_obj and len(new_obj) > 0:
            new_keys = set(new_obj.keys())

        keys = old_keys | new_keys

        result = {'_add': {}, '_delete': {}, '_update': {}}
        for attribute_name in keys:

            # old_obj is missing

            if attribute_name not in old_obj:
                result['_add'][attribute_name] = new_obj[attribute_name]
            elif attribute_name not in new_obj:

            # new_obj is missing

                result['_delete'][attribute_name] = \
                    old_obj[attribute_name]
            else:
                res = self._diff_objects(old_obj[attribute_name],
                                         new_obj[attribute_name])
                if res is not None:
                    result['_update'][attribute_name] = res

        return self._collate_results(result)

    def diff_resourcemodel(self, old_obj=None, new_obj=None):
        """
        Method to check diff of two resource model types

        As we are processing two ResourceModel objects both objects should be of same type
        """

        if not old_obj and hasattr(self, 'old_modelobj'):
            old_obj = self.old_modelobj
        if not new_obj and hasattr(self, 'new_modelobj'):
            new_obj = self.new_modelobj

        old_obj_spec_dict = old_obj.get_all_members()
        new_obj_spec_dict = new_obj.get_all_members()

        old_keys = set()
        new_keys = set()
        if old_obj_spec_dict and len(old_obj_spec_dict) > 0:
            old_keys = set(old_obj_spec_dict.keys())
        if new_obj_spec_dict and len(new_obj_spec_dict) > 0:
            new_keys = set(new_obj_spec_dict.keys())

        keys = old_keys | new_keys

        result = {'_add': {}, '_delete': {}, '_update': {}}
        for attribute_name in keys:

            # old_obj is missing

            if attribute_name not in old_keys:
                result['_add'][attribute_name] = getattr(new_obj,
                                                         attribute_name)
            elif attribute_name not in new_keys:

            # new_obj is missing

                result['_delete'][attribute_name] = getattr(old_obj,
                                                            attribute_name)
            else:
                res = self._diff_objects(getattr(old_obj,
                                                 attribute_name), getattr(new_obj,
                                                                          attribute_name))
                if res is not None:
                    result['_update'][attribute_name] = res

        return self._collate_results(result)
