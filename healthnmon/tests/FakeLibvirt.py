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


def open(name):
    return virConnect()


def openReadOnly(name):
    return virConnect()


def openAuth(uri, auth, flag):
    return virConnect()


def virEventRegisterDefaultImpl():
    pass


def virEventRunDefaultImpl():
    pass

VIR_DOMAIN_EVENT_ID_LIFECYCLE = 0
VIR_DOMAIN_EVENT_ID_REBOOT = 1
VIR_DOMAIN_EVENT_ID_DISK_CHANGE = 9


class virConnect:

    def __init__(self):
        self.storagePools = ['dirpool', 'default', 'iscsipool']

    def getCapabilities(self):
        return """<capabilities>

              <host>
                <uuid>34353438-3934-434e-3738-313630323543</uuid>
                <cpu>
                  <arch>x86_64</arch>
                  <model>Opteron_G2</model>
                  <vendor>AMD</vendor>
                  <topology sockets='2' cores='2' threads='1'/>
                  <feature name='cr8legacy'/>
                  <feature name='extapic'/>
                  <feature name='cmp_legacy'/>
                  <feature name='3dnow'/>
                  <feature name='3dnowext'/>
                  <feature name='fxsr_opt'/>
                  <feature name='mmxext'/>
                  <feature name='ht'/>
                  <feature name='vme'/>
                </cpu>
                <migration_features>
                  <live/>
                  <uri_transports>
                    <uri_transport>tcp</uri_transport>
                  </uri_transports>
                </migration_features>
                <secmodel>
                  <model>apparmor</model>
                  <doi>0</doi>
                </secmodel>
              </host>

              <guest>
                <os_type>hvm</os_type>
                <arch name='i686'>
                  <wordsize>32</wordsize>
                  <emulator>/usr/bin/qemu</emulator>
                  <machine>pc-0.14</machine>
                  <machine canonical='pc-0.14'>pc</machine>
                  <machine>pc-0.13</machine>
                  <machine>pc-0.12</machine>
                  <machine>pc-0.11</machine>
                  <machine>pc-0.10</machine>
                  <machine>isapc</machine>
                  <domain type='qemu'>
                  </domain>
                </arch>
                <features>
                  <cpuselection/>
                  <deviceboot/>
                  <pae/>
                  <nonpae/>
                  <acpi default='on' toggle='yes'/>
                  <apic default='on' toggle='no'/>
                </features>
              </guest>

              <guest>
                <os_type>hvm</os_type>
                <arch name='x86_64'>
                  <wordsize>64</wordsize>
                  <emulator>/usr/bin/qemu-system-x86_64</emulator>
                  <machine>pc-0.14</machine>
                  <machine canonical='pc-0.14'>pc</machine>
                  <machine>pc-0.13</machine>
                  <machine>pc-0.12</machine>
                  <machine>pc-0.11</machine>
                  <machine>pc-0.10</machine>
                  <machine>isapc</machine>
                  <domain type='qemu'>
                  </domain>
                </arch>
                <features>
                  <cpuselection/>
                  <deviceboot/>
                  <acpi default='on' toggle='yes'/>
                  <apic default='on' toggle='no'/>
                </features>
              </guest>

            </capabilities>
            """

    def getSysinfo(self, flag):
        return """<sysinfo type='smbios'>
                              <bios>
                                <entry name='vendor'>HP</entry>
                                <entry name='version'>A13</entry>
                                <entry name='date'>02/21/2008</entry>
                              </bios>
                              <system>
                                <entry name='manufacturer'>HP</entry>
                                <entry name='product'>ProLiant BL465c G1  </entry>
                                <entry name='version'>Not Specified</entry>
                                <entry name='serial'>CN7816025C      </entry>
                                <entry name='uuid'>34353438-3934-434E-3738-313630323543</entry>
                                <entry name='sku'>454894-B21      </entry>
                                <entry name='family'>ProLiant</entry>
                              </system>
                            </sysinfo>"""

    def getInfo(self):
        return [
            'x86_64',
            3960,
            4,
            1000,
            1,
            2,
            2,
            1,
            ]

    def getHostname(self):
        return 'ubuntu164.vmm.hp.com'

    def listDefinedDomains(self):
        return ['ReleaseBDevEnv']

    def listDomainsID(self):
        return [1]

    def lookupByName(self, name):
        return virDomain()

    def lookupByID(self, domId):
        return virDomain()

    def lookupByUUIDString(self, uuid):
        return virDomain()

    def storagePoolLookupByName(self, name):
        if name == 'default':
            return virStoragePool()
        elif name == 'nova-storage-pool':
            return virDirPool()
        else:
            return virStoragePoolInactive()

    def storageVolLookupByPath(self, name):
        return virStorageVol()

    def listStoragePools(self):
        return self.storagePools

    def listDefinedStoragePools(self):
        return ['inactivePool']

    def storagePoolDefineXML(self, xml, flag):
        self.storagePools.append('nova-storage-pool')
        return virDirPool()

    def listNetworks(self):
        return ['default']

    def listDefinedNetworks(self):
        return ['inactiveNetwork']

    def listInterfaces(self):
        return ['br100', 'eth0', 'lo']

    def listDefinedInterfaces(self):
        return ['inactiveInterface']

    def networkLookupByName(self, name):
        if name == 'default':
            return virLibvirtNetwork()
        elif name == 'staticNw':
            return virLibvirtStaticNw()
        else:
            return virLibvirtInactiveNw()

    def interfaceLookupByName(self, name):
        if name == 'br100':
            return virLibvirtInterface()
        elif name == 'eth0':
            return virLibvirtInterfaceEth0()
        elif name == 'inactiveInterface':
            return virLibvirtInterfaceInactive()
        else:
            return virLibvirtInterfaceLo()

    def getFreeMemory(self):
        return 0

    def getType(self):
        return 'QEMU'

    def getVersion(self):
        return 14001

    def domainEventRegisterAny(self, dom, eventID, cb, opaque):
        """Adds a Domain Event Callback. Registering for a domain
           callback will enable delivery of the events """
        return 1

    def domainEventDeregisterAny(self, callbackid):
        return 1

    def close(self):
        return 0


class virDomain:

    def UUIDString(self):
        return '25f04dd3-e924-02b2-9eac-876e3c943262'

    def XMLDesc(self, flag):
        return """<domain type='qemu' id='1'>
                  <name>TestVirtMgrVM7</name>
                  <uuid>25f04dd3-e924-02b2-9eac-876e3c943262</uuid>
                  <memory>1048576</memory>
                  <currentMemory>1048576</currentMemory>
                  <vcpu>1</vcpu>
                  <os>
                    <type arch='x86_64' machine='pc-0.14'>hvm</type>
                    <boot dev='hd'/>
                  </os>
                  <features>
                    <acpi/>
                    <apic/>
                    <pae/>
                  </features>
                  <clock offset='utc'/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>
                    <emulator>/usr/bin/qemu-system-x86_64</emulator>
                    <disk type='file' device='disk'>
                      <driver name='qemu' type='raw'/>
                      <source file='/var/lib/libvirt/images/TestVirtMgrVM7.img'/>
                      <target dev='hda' bus='scsi'/>
                      <alias name='ide0-0-0'/>
                      <address type='drive' controller='0' bus='0' unit='0'/>
                    </disk>
                    <disk type='block' device='disk'>
                      <driver name='qemu' type='raw'/>
                      <source dev='/dev/disk/by-path/ip-10.10.4.21:3260-iscsi-iqn.2010-10.org.openstack:volume-00000001-lun-1'/>
                      <target dev='vdb' bus='virtio'/>
                      <alias name='virtio-disk1'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
                    </disk>
                      <disk type='block' device='disk'>
                      <driver name='qemu' type='raw'/>
                      <source junk='/dev/disk/by-path/ip-10.10.4.21:3260-iscsi-iqn.2010-10.org.openstack:volume-00000001-lun-1'/>
                      <target dev='vdb' bus='virtio'/>
                      <alias name='virtio-disk1'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
                    </disk>
                    <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file='/home/ubuntu164/vmdks/ubuntu-11.10-desktop-i386.iso'/>
                      <target dev='hdc' bus='ide'/>
                      <readonly/>
                      <alias name='ide0-1-0'/>
                      <address type='drive' controller='0' bus='1' unit='0'/>
                    </disk>
                    <controller type='scsi' index='0'>
                      <alias name='ide0'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
                    </controller>
                    <interface type='network'>
                      <mac address='52:54:00:4c:82:63'/>
                      <source network='default'/>
                      <target dev='vnet0'/>
                      <alias name='net0'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
                       <filterref filter='nova-instance-instance-000002f2-fa163e7ab3f9'>
                        <parameter name='DHCPSERVER' value='10.1.1.22'/>
                        <parameter name='IP' value='10.1.1.19'/>
                      </filterref>
                    </interface>
                    <interface type='bridge'>
                      <mac address='52:54:00:4c:82:63'/>
                      <source network='default'/>
                      <target dev='br100'/>
                      <alias name='net0'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
                      <filterref filter='nova-instance-instance-000002f2-fa163e1b7489'>
                        <parameter name='DHCPSERVER' value='10.2.1.22'/>
                        <parameter name='IP' value='10.2.1.20'/>
                      </filterref>
                    </interface>
                    <serial type='pty'>
                      <source path='/dev/pts/1'/>
                      <target port='0'/>
                      <alias name='serial0'/>
                    </serial>
                    <console type='pty' tty='/dev/pts/1'>
                      <source path='/dev/pts/1'/>
                      <target type='serial' port='0'/>
                      <alias name='serial0'/>
                    </console>
                    <input type='mouse' bus='ps2'/>
                    <graphics type='vnc' port='5900' autoport='yes'/>
                    <sound model='ich6'>
                      <alias name='sound0'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
                    </sound>
                    <video>
                      <model type='cirrus' vram='9216' heads='1'/>
                      <alias name='video0'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
                    </video>
                    <memballoon model='virtio'>
                      <alias name='balloon0'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
                    </memballoon>
                  </devices>
                  <seclabel type='dynamic' model='apparmor'>
                    <label>libvirt-25f04dd3-e924-02b2-9eac-876e3c943262</label>
                    <imagelabel>libvirt-25f04dd3-e924-02b2-9eac-876e3c943262</imagelabel>
                  </seclabel>
                </domain>
                """

    def name(self):
        return 'TestVirtMgrVM7'

    def ID(self):
        return 1

    def blockInfo(self, path, flags):
        return [100, 200, 300]

    def blockStats(self, path):
        return (6492L, 191928832L, 1600L, 14091264L, -1L)

    def interfaceStats(self, path):
        return (
            56821L,
            1063L,
            0L,
            0L,
            4894L,
            30L,
            0L,
            0L,
            )

    def info(self):
        return [1, 2097152L, 2097152L, 1, 372280000000L]

    def state(self, flag):
        return [1, 1]

    def isActive(self):
        return 0

    def autostart(self):
        return 1


class virStoragePool:

    def UUIDString(self):
        return '95f7101b-892c-c388-867a-8340e5fea27a'

    def XMLDesc(self, flag):
        return """<pool type='dir'>
                                  <name>default</name>
                                  <uuid>95f7101b-892c-c388-867a-8340e5fea27a</uuid>
                                  <capacity>113595187200</capacity>
                                  <allocation>11105746944</allocation>
                                  <available>102489440256</available>
                                  <source>
                                  </source>
                                  <target>
                                    <path>/var/lib/libvirt/images</path>
                                    <permissions>
                                      <mode>0700</mode>
                                      <owner>-1</owner>
                                      <group>-1</group>
                                    </permissions>
                                  </target>
                                </pool>"""

    def name(self):
        return 'default'

    def isActive(self):
        return 1

    def refresh(self, data):
        pass


class virDirPool:
    def UUIDString(self):
        return '95f7101b-892c-c388-867a-8340e5feadir'

    def XMLDesc(self, flag):
        return """<pool type='dir'>
                                  <name>nova-storage-pool</name>
                                  <uuid>95f7101b-892c-c388-867a-8340e5feadir</uuid>
                                  <capacity>113595187200</capacity>
                                  <allocation>11105746944</allocation>
                                  <available>102489440256</available>
                                  <source>
                                  </source>
                                  <target>
                                    <path>/var/lib/nova/instances</path>
                                    <permissions>
                                      <mode>0700</mode>
                                      <owner>-1</owner>
                                      <group>-1</group>
                                    </permissions>
                                  </target>
                                </pool>"""

    def name(self):
        return 'nova-storage-pool'

    def setAutostart(self, flag):
        pass

    def build(self, flag):
        pass

    def create(self, flag):
        pass

    def isActive(self):
        return 1

    def refresh(self, data):
        pass


class virStoragePoolInactive:

    def UUIDString(self):
        return '95f7101b-892c-c388-867a-8340e5fea27x'

    def XMLDesc(self, flag):
        return """<pool type='dir'>
                                  <name>inactivePool</name>
                                  <uuid>95f7101b-892c-c388-867a-8340e5fea27a</uuid>
                                  <capacity>113595187200</capacity>
                                  <allocation>11105746944</allocation>
                                  <available>102489440256</available>
                                  <source>
                                  </source>
                                  <target>
                                    <path>/var/lib/libvirt/images</path>
                                    <permissions>
                                      <mode>0700</mode>
                                      <owner>-1</owner>
                                      <group>-1</group>
                                    </permissions>
                                  </target>
                                </pool>"""

    def name(self):
        return 'inactivePool'

    def isActive(self):
        return 0

    def refresh(self, data):
        pass


class virStorageVol:

    def storagePoolLookupByVolume(self):
        return virStoragePool()

    def UUIDString(self):
        return '95f7101b-892c-c388-867a-8340e5fea27x'


class virLibvirtNetwork:

    def UUIDString(self):
        return '3fbfbefb-17dd-07aa-2dac-13afbedf3be3'

    def XMLDesc(self, flag):
        return """<network>
                        <name>default</name>
                        <uuid>3fbfbefb-17dd-07aa-2dac-13afbedf3be3</uuid>
                        <forward mode='nat'/>
                        <bridge name='virbr0' stp='on' delay='0' />
                        <mac address='52:54:00:34:14:AE'/> \
                        <ip address='192.168.122.1' netmask='255.255.255.0'>
                            <dhcp>
                                <range start='192.168.122.2' end='192.168.122.254' />
                                </dhcp>
                        </ip>
                        </network>"""

    def name(self):
        return 'default'

    def autostart(self):
        return 0

    def isActive(self):
        return 1


class virLibvirtStaticNw:

    def UUIDString(self):
        return '3fbfbefb-17dd-07aa-2dac-13afbedf3be9'

    def XMLDesc(self, flag):
        return """<network>
                        <name>staticNw</name>
                        <uuid>3fbfbefb-17dd-07aa-2dac-13afbedf3be3</uuid>
                        <forward mode='nat'/>
                        <bridge name='virbr0' stp='on' delay='0' />
                        <mac address='52:54:00:34:14:AE'/> \
                        <ip address='192.168.122.1' netmask='255.255.255.0'>
                        </ip>
                        </network>"""

    def name(self):
        return 'staticNw'

    def autostart(self):
        return 0

    def isActive(self):
        return 1


class virLibvirtInactiveNw:

    def UUIDString(self):
        return '3fbfbefb-17dd-07aa-2dac-13afbedf3be9'

    def XMLDesc(self, flag):
        return """<network>
                        <name>inactiveNetwork</name>
                        <uuid>3fbfbefb-17dd-07aa-2dac-13afbedf3be3</uuid>
                        <forward mode='nat'/>
                        <bridge name='virbr0' stp='on' delay='0' />
                        <mac address='52:54:00:34:14:AE'/> \
                        <ip address='192.168.122.1' netmask='255.255.255.0'>
                        </ip>
                        </network>"""

    def name(self):
        return 'inactiveNw'

    def autostart(self):
        return 1

    def isActive(self):
        return 0


# class virNetwork:
#
#    def networkLookupByVolume(self):
#        return virLibvirtNetwork()

class virLibvirtInterface:

    def XMLDesc(self, flag):
        return """<interface type='bridge' name='br100'>

                     <protocol family='ipv4'>
                        <ip address='10.1.1.3' prefix='24'/>
                        <ip address='10.1.1.14' prefix='24'/>
                      </protocol>
                      <protocol family='ipv6'>
                        <ip address='fe80::223:7dff:fe34:dbf0' prefix='64'/>
                      </protocol>
                      <bridge>
                        <interface type='ethernet' name='vnet0'>
                            <mac address='fe:54:00:12:e3:90'/> \
                        </interface> \
                        <interface type='ethernet' name='eth1'>
                            <mac address='00:23:7d:34:db:f0'/> \
                        </interface>
                       </bridge> \
                </interface>"""

    def name(self):
        return 'br100'

    def isActive(self):
        return 1

    def MACString(self):
        return '00:23:7d:34:db:f0'


class virLibvirtInterfaceEth0:

    def XMLDesc(self, flag):
        return """<interface type='ethernet' name='eth0'>
                    <mac address='00:23:7d:34:bb:e8'/>
                    <protocol family='ipv4'>
                        <ip address='10.10.155.140' prefix='16'/> \
                    </protocol>
                    <protocol family='ipv6'>
                        <ip address='fe80::223:7dff:fe34:bbe8' prefix='64'/> \
                    </protocol> \
                </interface> """


class virLibvirtInterfaceLo:

    def XMLDesc(self, flag):
        return """<interface type='ethernet' name='lo'>
                  <protocol family='ipv4'>
                    <ip address='127.0.0.1' prefix='8'/>
                    <ip address='169.254.169.254' prefix='32'/>
                  </protocol>
                  <protocol family='ipv6'>
                    <ip address='::1' prefix='128'/>
                  </protocol>
                </interface> """


class virLibvirtInterfaceInactive:

    def XMLDesc(self, flag):
        return """<interface type='bridge' name='inactiveInterface'>
                      <protocol family='ipv6'>
                        <ip address='fe80::223:7dff:fe34:dbf0' prefix='64'/>
                      </protocol>
                      <bridge>
                        <interface type='ethernet' name='eth1'>
                            <mac address='00:23:7d:34:db:f0'/> \
                        </interface>
                        <interface type='ethernet' name='vnet0'>
                            <mac address='fe:54:00:12:e3:90'/> \
                        </interface> \
                       </bridge> \
                </interface>"""

    def name(self):
        return 'inactiveInterface'

    def isActive(self):
        return 0

    def MACString(self):
        return '00:23:7d:34:db:f1'


class libvirtError(Exception):

    def getDesc(self):
        return 'Error'

    def get_error_code(self):
        return 38

    def get_error_domain(self):
        return 13


VIR_CRED_AUTHNAME = 2
VIR_CRED_NOECHOPROMPT = 7

# virErrorDomain

VIR_ERR_SYSTEM_ERROR = 38
VIR_FROM_REMOTE = 13
VIR_FROM_RPC = 7
