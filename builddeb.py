# vim: tabstop=4 shiftwidth=4 softtabstop=4

#          (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
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
if not os.path.exists('tmp'):
    os.makedirs('tmp')
os.chdir('tmp')
tar_file = sys.argv[1]
if os.path.isfile(tar_file) is False:
        print 'Invalid path for the tar ball'
        sys.exit()
os.system('tar -xzf %s' % tar_file)
source_dir = sys.argv[1][:-7].split('/')[-1]
print 'Source_dir created = %s' % source_dir
os.system('cp -r ../debian %s' % source_dir)
os.chdir(source_dir)
os.system('dch --increment %s' % sys.argv[2])
res = os.system('debuild --no-tgz-check -us -uc')
if res != 0:
        print 'Build failed'
        sys.exit(1)
os.chdir('../')
files = os.listdir('.')
for fileName in files:
    if fileName.endswith(".deb"):
	if not os.path.exists('../target/debbuild'):
    		os.makedirs('../target/debbuild')
        os.system('mv %s ../target/debbuild' % fileName)
print 'Debian packages created successfully'
print 'Check in the debbuild directory'
print 'Now removing tmp directory'
os.chdir('../')
os.system('rm -rf tmp')
