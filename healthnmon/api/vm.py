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
from ..api import constants
from ..api import base
from ..resourcemodel import healthnmonResourceModel


LOG = logging.getLogger(__name__)


class VMController(base.Controller):

    """ Controller class for Vm resource extension """
    def __init__(self):
        ''' Initialize controller with resource specific param values '''
        base.Controller.__init__(self,
                                 constants.VM_COLLECTION_NAME,
                                 'vm',
                                 'Vm')

    def index(self, req):
        """ List all virtual machine as a simple list
            :param req: webob request
            :returns: simple list of virtual machine with appropriate
            resource links.
        """

        server_list = self.get_all_by_filters(req, api.vm_get_all_by_filters)
        if not server_list:
            server_list = []
        limited_list, collection_links = self.limited_by_marker(server_list,
                                                                req)
        return self._index(req, limited_list, collection_links)

    def detail(self, req):
        """
            List all virtual machines as a detailed list with appropriate
            resource links
            :param req: webob request
            :returns: webob response for detail list operation.
        """
        server_list = self.get_all_by_filters(req, api.vm_get_all_by_filters)
        if not server_list:
            server_list = []
        limited_list, collection_links = self.limited_by_marker(server_list,
                                                                req)
        return self._detail(req, limited_list, collection_links)

    def _get_resource_xml_with_links(self, req, vm):
        """ Get resource as xml updated with
            reference links to other resources.
            :param req: request object
            :param vm: vm object as per resource model
            :returns: (vm_xml, out_dict) tuple where,
                        vm_xml is the updated xml and
                        out_dict is a dictionary with keys as
                        the xpath of replaced entities and
                        value is the corresponding entity dict.
        """

        (ctx, proj_id) = util.get_project_context(req)
        vm_xml = util.dump_resource_xml(vm, self._model_name)
        out_dict = {}
        vm_xml_update = util.replace_with_links(vm_xml,
                self._get_resource_tag_dict_list(req.application_url,
                                               proj_id),
                out_dict)
        field_list = util.get_query_fields(req)
        if field_list != None:
            if 'utilization' in field_list:
                vm_xml_update = self._add_perf_data(vm.get_id(),
                        vm_xml_update, ctx)
            vm_xml_update = \
                util.get_select_elements_xml(vm_xml_update,
                    field_list, 'id')
        elif len(req.GET.getall('utilization')) > 0:
            vm_xml_update = self._add_perf_data(vm.get_id(),
                    vm_xml_update, ctx)
        return (vm_xml_update, out_dict)

    def _get_resource_tag_dict_list(self, application_url, proj_id):
        """ Get the list of tag dictionaries applicable to virtual machine
            :param application_url: application url from request
            :param proj_id: project id
            :returns: list of tag dictionaries for virtual machine
        """
        return   [{
            'tag': 'storageVolumeId',
            'tag_replacement': 'storagevolume',
            'tag_key': 'id',
            'tag_collection_url': os.path.join(application_url,
                    proj_id, constants.STORAGEVOLUME_COLLECTION_NAME),
            'tag_attrib': None,
            }, {
            'tag': 'vmHostId',
            'tag_replacement': 'vmhost',
            'tag_key': 'id',
            'tag_collection_url': os.path.join(application_url,
                    proj_id, constants.VMHOSTS_COLLECTION_NAME),
            'tag_attrib': None,
            }]

    def show(self, req, id):
        """ Display details for particular virtual machine
            identified by resource id.

            :param req: webob request
            :param id: unique id to identify virtual machine.
            :returns: complete resource details for the specified id and
            request.
        """
        try:
            LOG.debug(_('Show vm id : %s' % str(id)))
            (ctx, proj_id) = util.get_project_context(req)
            vm_list = api.vm_get_by_ids(ctx, [id])
            LOG.debug(_('Project id: %s Received vmhosts from the database'
                       % proj_id))
            if vm_list:
                return self._show(req, vm_list[0])
        except Exception, err:
            LOG.error(_('Exception while fetching data from healthnmon api %s'
                       % str(err)), exc_info=1)
        return HTTPNotFound()

    def _add_perf_data(
        self,
        vm_id,
        input_xml,
        ctx,
        ):
        ''' Append virtual machine resource utilization data
            :param vm_id: virtual machine id
            :param input_xml: virtual machine detail xml
            :param ctx: request context
            :returns: virtual machine detail xml appended with
            resource utilization
        '''
        perf_data = api.get_vm_utilization(ctx, vm_id)
        attr_dict = perf_data['ResourceUtilization']
        resource_obj = healthnmonResourceModel.ResourceUtilization()
        util.set_select_attributes(resource_obj, attr_dict)
        utilization_xml = util.dump_resource_xml(resource_obj,
                'utilization')
        LOG.debug(_('Utilization xml: %s' % utilization_xml))
        return util.append_xml_as_child(input_xml, utilization_xml)
