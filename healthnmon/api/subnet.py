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

from ..api import util
from ..api import constants
from ..api import base
from .. import healthnmon_api as api
from .. import log as logging
from webob.exc import HTTPNotFound

LOG = logging.getLogger(__name__)


class SubnetController(base.Controller):

    '''
    Subnet controller for handling subnet
    resource api calls.
    '''
    def __init__(self):
        ''' Initialize controller with resource specific param values '''
        base.Controller.__init__(self,
                                 constants.SUBNET_COLLECTION_NAME,
                                 'subnet',
                                 'Subnet')

    def index(self, req):
        """ List all subnets as a simple list
        :param req: webob request
        :returns: simple list of subnets with resource links to each subnet.
        """
        subnet_list = self.get_all_by_filters(req,
                                              api.subnet_get_all_by_filters)
        if not subnet_list:
            subnet_list = []
        limited_list, collection_links = self.limited_by_marker(
            subnet_list,
            req)
        return self._index(req, limited_list, collection_links)

    def detail(self, req):
        """
            List all subnets as a detailed list with appropriate
            resource links
            :param req: webob request
            :returns: webob response for detail list operation.
        """

        subnet_list = self.get_all_by_filters(req,
                                              api.subnet_get_all_by_filters)
        if not subnet_list:
            subnet_list = []
        limited_list, collection_links = self.limited_by_marker(
            subnet_list,
            req)
        return self._detail(req, limited_list, collection_links)

    def show(self, req, id):
        """ Display details for particular subnet
            identified by resource id.

            :param req: webob request
            :param id: unique id to identify subnet resource.
            :returns: complete subnet resource details for the specified id and
            request.
        """
        try:
            LOG.debug(_('Show subnet id : %s' % str(id)))
            (ctx, proj_id) = util.get_project_context(req)
            subnet_list = api.subnet_get_by_ids(ctx, [id])
            LOG.debug(_('Project id: %s Received subnets from the database'
                        % proj_id))
            if subnet_list:
                return self._show(req, subnet_list[0])
        except Exception, err:
            LOG.error(_('Exception while fetching data from healthnmon api %s'
                        % str(err)), exc_info=1)

        return HTTPNotFound()
