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


class SSHClient (object):

    def __init__(self):
        pass

    def set_missing_host_key_policy(self, policy):
        pass

    def connect(self, hostname, port=None, username=None, password=None, pkey=None,
                key_filename=None, timeout=None, allow_agent=True, look_for_keys=True,
                compress=False):
        pass

    def exec_command(self, cmd):
        stdin = FakeSSHOutput("in")
        stdout = FakeSSHOutput("out")
        stderr = FakeSSHOutput("err")
        return stdin, stdout, stderr

    def close(self):
        pass


class FakeSSHOutput(object):

    memstats = ['total  :              2053208 kB\n', 'free   :               711092 kB\n', 'buffers:               171236 kB\n', 'cached :               266116 kB\n', '\n']

    def __init__(self, type):
        self.type = type

    def readlines(self):
        if self.type == "in":
            return []
        elif self.type == 'out':
            return self.memstats
        elif self.type == 'err':
            return []

        return self.memstats
