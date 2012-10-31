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


CPU_PROFILE_CALLED_FUNCTION = []
MEMORY_PROFILE_CALLED_FUNCTION = []


def example_cpu_profile_decorator(name, function):
    """ decorator for cpu profile which is used for testing helper.profile_cputime

        :param name: name of the function
        :param function: - object of the function
        :returns: function -- decorated function
    """
    def profile_cputime(*args, **kwarg):
        CPU_PROFILE_CALLED_FUNCTION.append(name)
        return function(*args, **kwarg)
    return profile_cputime


def example_memory_profile_decorator(name, function):
    """ decorator for cpu profile which is used for testing helper.profile_memory

        :param name: name of the function
        :param function: - object of the function
        :returns: function -- decorated function
    """
    def profile_memory(*args, **kwarg):
        MEMORY_PROFILE_CALLED_FUNCTION.append(name)
        return function(*args, **kwarg)
    return profile_memory
