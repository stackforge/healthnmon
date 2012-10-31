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
import sys

from nova import exception
from nova import flags

from migrate.versioning import api as versioning_api

try:
    from migrate.versioning import exceptions as versioning_exceptions
except ImportError:
    try:

        # python-migration changed location of exceptions after 1.6.3
        # See LP Bug #717467

        from migrate import exceptions as versioning_exceptions
    except ImportError:
        sys.exit(_('python-migrate is not installed. Exiting.'))

FLAGS = flags.FLAGS


def db_sync(version=None):
    if version is not None:
        try:
            version = int(version)
        except ValueError:
            raise exception.Error(_('version should be an integer'))

    current_version = db_version()
    repo_path = _find_migrate_repo()
    if version is None or version > current_version:
        return versioning_api.upgrade(FLAGS.sql_connection, repo_path,
                version)
    else:
        return versioning_api.downgrade(FLAGS.sql_connection,
                repo_path, version)


def db_version():
    repo_path = _find_migrate_repo()
    try:
        return versioning_api.db_version(FLAGS.sql_connection,
                repo_path)
    except versioning_exceptions.DatabaseNotControlledError:

        # and set up version_control appropriately

        return db_version_control(0)


def db_version_control(version=None):
    repo_path = _find_migrate_repo()
    versioning_api.version_control(FLAGS.sql_connection, repo_path,
                                   version)
    return version


def _find_migrate_repo():
    """Get the path for the migrate repository."""

    path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'migrate_repo')
    assert os.path.exists(path)
    return path
