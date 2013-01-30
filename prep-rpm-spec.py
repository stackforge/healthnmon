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

import os
import re
import glob
import subprocess

from healthnmon.version import version_info

def get_version():
    version=version_info.canonical_version_string()
    print version
    return version

def exec_command(command):
    """
    Executes command and returns output. Raises exception if returncode > 0
    """
    print "Execute:", command
    cmdio = subprocess.Popen(command,
                             shell=True,
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
    output = cmdio.communicate()
    if cmdio.returncode > 0:
        errstr = "%s [%s]" % (command, output[1])
        raise CommandFailed(errstr)
    return output[0]

def prep_rpm_spec(specfile):
    """
    Returns the patched source directory under BUILD
    """
    cwd = os.getcwd()
    #specfile = os.path.join(os.path.join(cwd, 'rpm'), specfile)
    try:
        exec_command("find ./rpm -name %s -exec sed -i 's/2013.1/%s/g' {} \;" % (specfile, get_version()))
    except Exception, reason:
        import traceback, sys
        traceback.print_exc(file=sys.stdout)
        raise BuildFailed(reason)

prep_rpm_spec("healthnmon.spec")
