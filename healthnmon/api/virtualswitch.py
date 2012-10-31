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
from webob.exc import HTTPNotFound

from .. import log as logging
from .. import healthnmon_api as api
from ..api import util
from ..api import base
from ..api import constants

LOG = logging.getLogger(__name__)


class VirtualSwitchController(base.Controller):

    """ Controller class for Virtual Switch resource extension """

    def __init__(self):
        ''' Initialize controller with resource specific param values '''
        base.Controller.__init__(self,
                                 constants.VIRTUAL_SWITCH_COLLECTION_NAME,
                                 'virtualswitch',
                                 'VirtualSwitch')

    #NOTE(siva): virtual switch type not included in simple list output.
    def index(self, req):
        """ List all virtual switches as a simple list
            :param req: webob request
            :returns: simple list of virtual switches with resource links to
            each virtual switch.
        """
        virtualswitch_list = self.get_all_by_filters(req,
                                        api.virtual_switch_get_all_by_filters)
        if not virtualswitch_list:
            virtualswitch_list = []
        limited_list, collection_links = self.limited_by_marker(\
                                                    virtualswitch_list,
                                                    req)
        return self._index(req, limited_list, collection_links)

    def detail(self, req):
        """
            List all virtual switches as a detailed list with appropriate
            resource links
            :param req: webob request
            :returns: webob response for detail list operation.
        """

        virtualswitch_list = self.get_all_by_filters(req,
                                        api.virtual_switch_get_all_by_filters)
        if not virtualswitch_list:
            virtualswitch_list = []
        limited_list, collection_links = self.limited_by_marker(\
                                                            virtualswitch_list,
                                                            req)
        return self._detail(req, limited_list, collection_links)

    def _get_resource_tag_dict_list(self, application_url, proj_id):
        """ Get the list of tag dictionaries applicable to the resource
            :param application_url: application url from request
            :param proj_id: project id
            :returns: list of tag dictionaries for the resource
        """
        return [{
            'tag': 'subnetIds',
            'tag_replacement': 'subnet',
            'tag_key': 'id',
            'tag_collection_url': os.path.join(application_url,
                    proj_id, constants.SUBNET_COLLECTION_NAME),
            'tag_attrib': None,
            }]

    def show(self, req, id):
        """ Display details for particular virtual_switch
            identified by resource id.

            :param req: webob request
            :param id: unique id to identify virtual_switch resource.
            :returns: complete virtual_switch resource details for the
            specified id and request.
        """
        try:
            LOG.debug(_('Show virtual_switch id : %s' % str(id)))
            (ctx, proj_id) = util.get_project_context(req)
            virtual_switch_list = api.virtual_switch_get_by_ids(ctx,
                    [id])
            LOG.debug(_('Project id: %s Received virtual switches from database'
                       % proj_id))
            if virtual_switch_list:
                return self._show(req, virtual_switch_list[0])
        except Exception, err:
            LOG.error(_('Exception while fetching data from healthnmon api %s'
                       % str(err)), exc_info=1)

        return HTTPNotFound()
