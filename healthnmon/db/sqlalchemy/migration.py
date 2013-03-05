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

import distutils.version as dist_version
import os

from healthnmon.db import migration
from nova.db.sqlalchemy.session import get_engine
from nova import exception
import migrate
from migrate.versioning import util as migrate_util
from migrate import exceptions as versioning_exceptions
from migrate.versioning import api as versioning_api
from migrate.versioning.repository import Repository

_REPOSITORY = None


@migrate_util.decorator
def patched_with_engine(f, *a, **kw):
    url = a[0]
    engine = migrate_util.construct_engine(url, **kw)

    try:
        kw['engine'] = engine
        return f(*a, **kw)
    finally:
        if isinstance(engine, migrate_util.Engine) and engine is not url:
            migrate_util.log.debug('Disposing SQLAlchemy engine %s', engine)
            engine.dispose()


MIN_PKG_VERSION = dist_version.StrictVersion('0.7.3')
if (not hasattr(migrate, '__version__') or
        dist_version.StrictVersion(migrate.__version__) < MIN_PKG_VERSION):
    migrate_util.with_engine = patched_with_engine


def db_sync(version=None):
    if version is not None:
        try:
            version = int(version)
        except ValueError:
            raise exception.NovaException(_("version should be an integer"))

    current_version = db_version()
    repository = _find_migrate_repo()
    if version is None or version > current_version:
        return versioning_api.upgrade(get_engine(), repository, version)
    else:
        return versioning_api.downgrade(get_engine(), repository,
                                        version)


def db_version():
    repository = _find_migrate_repo()
    try:
        return versioning_api.db_version(get_engine(), repository)
    except versioning_exceptions.DatabaseNotControlledError:
        return db_version_control(migration.INIT_VERSION)


def db_version_control(version=None):
    repository = _find_migrate_repo()
    versioning_api.version_control(get_engine(), repository, version)
    return version


def _find_migrate_repo():
    """Get the path for the migrate repository."""
    global _REPOSITORY
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'migrate_repo')
    assert os.path.exists(path)
    if _REPOSITORY is None:
        _REPOSITORY = Repository(path)
    return _REPOSITORY
