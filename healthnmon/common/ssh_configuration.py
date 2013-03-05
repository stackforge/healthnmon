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

import sys
import os
import pwd
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko
import subprocess
import time
import socket
import libvirt
from healthnmon import log
from nova import crypto

LOG = log.getLogger('healthnmon.common.sshConfiguration')

"""
    Find's nova Home path
"""


def get_nova_home():
    """
    retrieve home path of nova . By default it is /var/lib/nova
    """

    nova_home = pwd.getpwnam('nova').pw_dir
    LOG.debug(_('Nova Home Directory' + nova_home))
    return nova_home


"""
Find's the current user
"""


def whoami():
    return pwd.getpwuid(os.getuid())[0]


'''
    Change the user execution Id.
    This will work when running as root and want to become somebody else
    '''


def change_user(name):
    uid = pwd.getpwnam(name).pw_uid
    gid = pwd.getpwnam(name).pw_gid
    os.setgid(gid)
    os.setuid(uid)


'''
    Validate the appliance and set all the parameters if required
'''


def is_valid_appliance():

    nova_home = get_nova_home()
    '    Change to user nova    '
    LOG.debug(_('Executing as ' + whoami()))
    if whoami() == 'root':
        change_user('nova')

    if whoami() != 'nova':
        LOG.debug(_('nova does not exists'))
        return False

    if os.path.exists(nova_home) is False:
        '''
        nova does not exists.Exiting now
        #todo : sys.exit()
        '''
        return False

    #    Check if the id_rsa and id_rsa.pub already exists.
    #    If they exist don't generate new keys"

    if not os.path.exists(os.path.join(nova_home + '/.ssh/')):
        os.makedirs(os.path.join(nova_home + '/.ssh/'), 01700)

    if os.path.isfile(
        os.path.join(nova_home + '/.ssh/id_rsa.pub')) is False and \
            os.path.isfile(os.path.join(nova_home + '/.ssh/id_rsa')) is False:
        '    Generate id_rsa and id_rsa.pub files. '
        '    This will be stored in $NOVAHOME/.ssh/ '
        '    use nova'
        private_key, public_key, _fingerprint = crypto.generate_key_pair()
        pub_file = open(os.path.join(nova_home + '/.ssh/id_rsa.pub'), "w+")
        pub_file.writelines(public_key)
        pub_file.close()

        private_file = open(os.path.join(nova_home + '/.ssh/id_rsa'), "w+")
        private_file.writelines(private_key)
        private_file.close()

        os.chmod(os.path.join(nova_home + '/.ssh/id_rsa.pub'), 0700)
        os.chmod(os.path.join(nova_home + '/.ssh/id_rsa'), 0700)
        # os.popen('ssh-keygen -t rsa', 'w').write(''' ''')
        LOG.debug(_('created new id_rsa and id_rsa.pub'))
    else:

        LOG.debug(_('id_rsa and id_rsa.pub exists'))

    '  create known_hosts file if it does not exist'
    if os.path.isfile(os.path.join(nova_home + '/.ssh/known_hosts')) is False:
        filename = os.path.join(nova_home + '/.ssh/known_hosts')
        handle = open(filename, 'w')
        handle.close
        os.chmod(os.path.join(nova_home + '/.ssh/known_hosts'), 0700)

    return True


def configure_host(hostname, user, password):

    sshConn = Client(hostname, user, password)

    ' Validate and configure appliance'
    if is_valid_appliance() is True:

        ' Test Connection with host '
        if sshConn.test_connection_auth() == 'False':
            print 'Cannot connect to host'
            return

        '    nova home path    '
        nova_home = get_nova_home()

        sftp = sshConn.get_ftp_connection()

        try:
            sftp.stat('.ssh/authorized_keys2')
        except:
            try:
                sftp.stat('.ssh/')
            except IOError:

                LOG.debug(_('.ssh folder does not exists on Host. ' +
                            'Creating .ssh folder'))
                try:
                    sftp.mkdir('.ssh/')
                    ' folder created. Now change permissions '
                    sshConn.exec_command('chmod 700 .ssh')
                except IOError:
                    pass

            ' Now check if authorized_keys2 files exists. '
            ' If not create it and change file permissions    '
            try:
                sftp.stat('.ssh/authorized_keys2')
            except IOError:

                LOG.debug(_('authorized_keys2 file does not exists on Host. ' +
                            'Creating authorized_keys2 filer'))
                try:
                    sftp.file('.ssh/authorized_keys2', ' x')
                    ' file created. Now change permissions '
                    sshConn.exec_command('chmod 700 .ssh/authorized_keys2')
                except IOError:
                    pass

        '   Create a temp directory    '
        try:
            LOG.debug(_('tempPubKey'))
            sftp.mkdir('tempPubKey')
        except IOError:

            'delete this folder and recreate it'
            sshConn.exec_command('rm -rf tempPubKey')
            sftp.mkdir('tempPubKey')

        ' Transfer the id_rsa.pub to kvm host '
        sftp.put(os.path.join(
            nova_home + '/.ssh/id_rsa.pub'), 'tempPubKey/id_rsa.pub')

        ' Append tempPubKey/id_rsa.pub to .ssh/authorized_keys2 '
        sshConn.exec_command(
            'cat tempPubKey/id_rsa.pub >> .ssh/authorized_keys2')

        sftp.close()
        '    delete the temp directory    '
        sshConn.exec_command('rm -rf tempPubKey')

        ' Verify the libvirt Connection'
        verify_libvirt_connection(user, hostname)


'''
    Verify Libvirt connection with the kvm Host
'''


def verify_libvirt_connection(user, hostname):

    try:
        conn = libvirt.open(
            'qemu+ssh://' + str(user) + '@' + str(hostname) + '/system')
        if isinstance(conn, libvirt.virConnect):
            print 'SSH successfully configured'
    except libvirt.libvirtError:
        print 'Error connecting to remote libvirt'


'''
This class implements the ssh client with the host
'''


class Client(object):

    def __init__(self, host, username, password, timeout=10):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = int(timeout)

    def _get_ssh_connection(self):
        """Returns an ssh connection to the specified host"""

        _timeout = True
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        nova_home = get_nova_home()
        ssh.load_host_keys(os.path.join(nova_home + '/.ssh/known_hosts'))
        _start_time = time.time()

        while not self._is_timed_out(self.timeout, _start_time):
            try:
                ssh.connect(self.host, username=self.username,
                            password=self.password,
                            look_for_keys=False, timeout=20)
                _timeout = False
                break
            except socket.error:
                continue
            except paramiko.AuthenticationException:
                time.sleep(15)
                continue
        if _timeout:
            print 'SSH connection timed out. Cannot Connect to '
            + str(self.username) + '@' + str(self.host)
            sys.exit(0)
        return ssh

    def get_ftp_connection(self):
        transport = paramiko.Transport(self.host)
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp

    def _is_timed_out(self, timeout, start_time):
        return time.time() - timeout > start_time

    def connect_until_closed(self):
        """Connect to the server and wait until connection is lost"""

        try:
            ssh = self._get_ssh_connection()
            _transport = ssh.get_transport()
            _start_time = time.time()
            _timed_out = self._is_timed_out(self.timeout, _start_time)
            while _transport.is_active() and not _timed_out:
                time.sleep(5)
                _timed_out = self._is_timed_out(self.timeout,
                                                _start_time)
            ssh.close()
        except (EOFError, paramiko.AuthenticationException, socket.error):
            return

    def exec_command(self, cmd):
        """Execute the specified command on the server.

        :returns: data read from standard output of the command

        """

        ssh = self._get_ssh_connection()
        (_stdin, stdout, _stderr) = ssh.exec_command(cmd)
        output = stdout.read()
        ssh.close()
        return output

    def test_connection_auth(self):
        """ Returns true if ssh can connect to server"""

        try:
            connection = self._get_ssh_connection()
            connection.close()
        except paramiko.AuthenticationException:
            return False

        return True
