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
:mod:`healthnmon` -- Health and Monitoring module for cloud
===================================================================

.. synopsis:: Health and Monitoring module for cloud
.. moduleauthor:: Divakar Padiyar Nandavar <divakar.padiyar-nandavar@hp.com>
.. moduleauthor:: Suryanarayana Raju <snraju@hp.com>
"""

import os


def get_healthnmon_location():
    """ Get the location of the healthnmon package
    """

    return os.path.join(os.path.dirname(__file__))
