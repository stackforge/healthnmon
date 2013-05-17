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

import setuptools

from healthnmon.openstack.common import setup
from healthnmon.version import version_info as version

requires = setup.parse_requirements()
depend_links = setup.parse_dependency_links()

setuptools.setup(
    name='healthnmon',
    version=version.get_version("healthnmon", "2013.1"),
    description='Healthnmon project provides health and'
                ' monitoring service for cloud',
    author='healthnmon',
    author_email='healthnmon@lists.launchpad.net',
    url='https://launchpad.net/healthnmon/',
    packages=setuptools.find_packages(exclude=['bin']),
    cmdclass=setup.get_cmdclass(),
    include_package_data=True,
    install_requires=requires,
    dependency_links=depend_links,
    test_suite='nose.collector',
    scripts=['bin/healthnmon', 'bin/healthnmon-manage'],
    py_modules=[],
)
