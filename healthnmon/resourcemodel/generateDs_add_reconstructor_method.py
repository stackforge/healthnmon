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

"""generateDs user methods spec module.

This module will be used by generateDs to add
SQLAlchemy reconstructor methods to generated model classes.
All the fields in model classes may not have a alchemy mapping
The reconstructor method will add unmapped fields to the SQLAlchemy constructed objects.

"""

import re

# MethodSpec class used by generateDs.
# See http://www.rexx.com/~dkuhlman/generateDS.html#user-methods for more details.


class MethodSpec(object):

    def __init__(
        self,
        name='',
        source='',
        class_names='',
        class_names_compiled=None,
    ):
        """MethodSpec -- A specification of a method.
        Member variables:
            name -- The method name
            source -- The source code for the method.  Must be
                indented to fit in a class definition.
            class_names -- A regular expression that must match the
                class names in which the method is to be inserted.
            class_names_compiled -- The compiled regex in class_names.
                generateDS.py will do this compile for you.
        """

        self.name = name
        self.source = source
        if class_names is None:
            self.class_names = ('.*',)
        else:
            self.class_names = class_names
        if class_names_compiled is None:
            self.class_names_compiled = re.compile(self.class_names)
        else:
            self.class_names_compiled = class_names_compiled

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_source(self):
        return self.source

    def set_source(self, source):
        self.source = source

    def get_class_names(self):
        return self.class_names

    def set_class_names(self, class_names):
        self.class_names = class_names
        self.class_names_compiled = re.compile(class_names)

    def get_class_names_compiled(self):
        return self.class_names_compiled

    def set_class_names_compiled(self, class_names_compiled):
        self.class_names_compiled = class_names_compiled

    def match_name(self, class_name):
        """Match against the name of the class currently being generated.
        If this method returns True, the method will be inserted in
          the generated class.
        """

        if self.class_names_compiled.search(class_name):
            return True
        else:
            return False

    def get_interpolated_source(self, values_dict):
        """Get the method source code, interpolating values from values_dict
        into it.  The source returned by this method is inserted into
        the generated class.
        """

        source = self.source % values_dict
        return source

    def show(self):
        print 'specification:'
        print '    name: %s' % (self.name,)
        print self.source
        print '    class_names: %s' % (self.class_names,)
        print '    names pat  : %s' \
            % (self.class_names_compiled.pattern,)


#
# Method specification for getting the member details of the class hierarchy recursively
#

getallmems_method_spec = MethodSpec(name='get_all_members',
                                    source='''\
    @classmethod
    def get_all_members(cls):
        member_items = %(class_name)s.member_data_items_
        if %(class_name)s.superclass != None:
            member_items.update(%(class_name)s.superclass.get_all_members())
        return member_items
''',
                                    class_names=r'^.*$')  # Attach to all classes

# Method specification for adding reconstructor method

recon_method_spec = MethodSpec(name='init_loader',
                               source='''\
    from sqlalchemy import orm
    @orm.reconstructor
    def init_loader(self):
        from sqlalchemy import orm
        objMapper = orm.object_mapper(self)
        containedKeys = self.__dict__
        requiredkeys = %(class_name)s.get_all_members()
        self.extensiontype_ = None
        for requiredkey in requiredkeys:
            mappedProp = None
            try:
                mappedProp = objMapper.get_property(requiredkey)
            except Exception:
                mappedProp = None
            if not mappedProp :
                if not containedKeys.has_key(requiredkey):
                    if requiredkeys[requiredkey].get_container() == 1:
                        setattr(self, requiredkey, [])
                    else:
                        setattr(self, requiredkey, None)
''',
                               class_names=r'^.*$')  # Attach to all classes

#
# Provide a list of method specifications.
# As per generateDs framework this list of specifications must be named METHOD_SPECS.
#

METHOD_SPECS = (getallmems_method_spec, recon_method_spec)


def test():
    for spec in METHOD_SPECS:
        spec.show()


def main():
    test()


if __name__ == '__main__':
    main()
