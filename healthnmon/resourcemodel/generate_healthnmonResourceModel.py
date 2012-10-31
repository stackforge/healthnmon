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
Script to generate healthnmonResourceModel.py file using generateDs
"""

import subprocess
import sys


def generate_resource_model():
    outfile = 'healthnmonResourceModel.py'
    xsdfile = 'healthnmonResourceModel.xsd'
    usermethodspec = 'generateDs_add_reconstructor_method'
    command = \
        'generateDS.py -o %s -m --member-specs=dict --user-methods=%s -q -f %s' \
        % (outfile, usermethodspec, xsdfile)

    print 'Generating %s from %s using generateDs' % (outfile, xsdfile)
    run_command(command.split())
    print 'Model file generation Succeeded'


def die(message, *args):
    print >> sys.stderr, message % args
    sys.exit(1)


def run_command_with_code(cmd, redirect_output=True,
                          check_exit_code=True):
    """
    Runs a command in an out-of-process shell, returning the
    output of that command.
    """

    if redirect_output:
        stdout = subprocess.PIPE
    else:
        stdout = None

    proc = subprocess.Popen(cmd, stdout=stdout)
    output = proc.communicate()[0]
    if check_exit_code and proc.returncode != 0:
        die('Command "%s" failed.\n%s', ' '.join(cmd), output)
    return (output, proc.returncode)


def run_command(cmd, redirect_output=True, check_exit_code=True):
    return run_command_with_code(cmd, redirect_output,
                                 check_exit_code)[0]


if __name__ == '__main__':
    generate_resource_model()
