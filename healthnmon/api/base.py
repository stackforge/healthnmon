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

'''
Base controller class for healthnmon extensions
'''
import json
import os
import webob
from webob import exc
from sqlalchemy import exc as sql_exc
from nova.exception import Invalid
from nova.api.openstack import common
from nova.openstack.common import timeutils

from ..api import util
from ..api import constants
from nova import flags
from nova.openstack.common import log as logging
from ..constants import DbConstants
from ..resourcemodel import healthnmonResourceModel
from types import *
import calendar


LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS


class Controller(common.ViewBuilder):
    '''
    Base controller class for healthnmon extensions. The methods in this class
    can be used by the derived resource controllers and actions to
    build and return webob responses for various API operations.
    '''
    def __init__(self, collection_name, member_name, model_name):
        ''' Initialize controller.
        :param collection_name: collection name for the resource
        :param member_name: member name(used for each member) in the resource
        :param model_name: healthnmon resource model class name for the
        resource
        '''
        self._collection_name = collection_name
        self._member_name = member_name
        self._model_name = model_name

    def _index(self, req, items, collection_links):
        """ List all resources as simple list with appropriate resource links
        :param req: webob request
        :param items: list of items to be listed
        :param collection_links: next/prev links for collection list.
        :returns: webob response for simple list operation.
        """
        item_dict_list = []
        for item in items:
            itemdict = {'id': item.get_id(),
                        'name': item.get_name(),
                        'links': self._get_links(req, item.get_id(), self._collection_name)
                        }
            item_dict_list.append(itemdict)
            LOG.debug(_('Appending item:' + str(itemdict)))
        resources_dict = {
            self._collection_name: item_dict_list
        }
        if collection_links:
            resources_dict[self._collection_name + '_links'] = collection_links
        # Create response
        nsmap = {None: constants.XMLNS_HEALTHNMON_EXTENSION_API,
                 'atom': constants.XMLNS_ATOM}
        if util.get_content_accept_type(req) == 'xml':
            return util.create_response('application/xml',
                    util.get_entity_list_xml(resources_dict, nsmap,
                                             self._collection_name,
                                             self._member_name))
        else:
            return util.create_response('application/json',
                    json.dumps(resources_dict))

    def _detail(self, req, items, collection_links):
        """ List all resources as a detailed list with appropriate
        resource links
        :param req: webob request
        :param items: list of items to be listed in detail
        :param collection_links: next/prev links for collection list.
        :returns: webob response for detail list operation.
        """
        content_type = util.get_content_accept_type(req)
        nsmap = {None: constants.XMLNS_HEALTHNMON_EXTENSION_API,
         'atom': constants.XMLNS_ATOM}
        # Create an empty parent xml
        parent_xml = util.get_entity_list_xml({self._collection_name: {}},
                                              nsmap,
                                              self._collection_name,
                                              self._model_name)
        item_list = []
        for item in items:
            (resource_xml, out_dict) = self._get_resource_xml_with_links(req, item)
            if content_type == 'xml':
                parent_xml = util.append_xml_as_child(parent_xml, resource_xml)
            else:
                converted_dict = util.xml_to_dict(resource_xml)
                if converted_dict is None:
                    converted_dict = {}
                resource_dict = {self._model_name: converted_dict}
                # The following is commented since we've incorporated
                # the required functionality in xml to dict method. A separate
                # call to this method, hence is not required.
                # util.update_dict_using_xpath(resource_dict, out_dict)
                LOG.debug(_('Dict after conversion %s'
                          % str(resource_dict)))
                LOG.debug(_('Appending item:' + str(resource_dict)))
                item_list.append(resource_dict[self._model_name])
        resources_dict = {self._collection_name: item_list}
        if collection_links:
            resources_dict[self._collection_name + '_links'] = collection_links
            for link in resources_dict[self._collection_name + '_links']:
                parent_xml = util.append_xml_as_child(parent_xml,
                                                      util.get_next_xml(link))
        if util.get_content_accept_type(req) == 'xml':
            return util.create_response('application/xml', parent_xml)
        else:
            return util.create_response('application/json',
                    json.dumps(resources_dict))

    def _get_resource_xml_with_links(self, req, item):
        """ Get item resource as xml updated with
            reference links to other resources.
            :param req: request object
            :param item: resource object as per resource model
            :returns: (resource_xml, out_dict) tuple where,
                        resource_xml is the updated xml and
                        out_dict is a dictionary with keys as
                        the xpath of replaced entities and
                        value is the corresponding entity dict.
        """
        proj_id = req.environ["nova.context"].project_id
        resource_xml = util.dump_resource_xml(item, self._model_name)
        out_dict = {}
        resource_xml_update = util.replace_with_links(resource_xml,
                self._get_resource_tag_dict_list(req.application_url,
                                               proj_id),
                out_dict)
        field_list = util.get_query_fields(req)
        if field_list != None:
            resource_xml_update = \
                util.get_select_elements_xml(resource_xml_update,
                    field_list, 'id')
        return (resource_xml_update, out_dict)

    def _get_resource_tag_dict_list(self, application_url, proj_id):
        """ Get the list of tag dictionaries applicable to
            resource
            :param application_url: application url from request
            :param proj_id: project id
            :returns: list of tag dictionaries for resources
        """
        return []

    def _show(self, req, item):
        """ Display details for particular resource
            identified by resource id.

            :param req: webob request
            :param item: resource item to be shown
            :returns: complete resource details for the specified item and
            request.
        """
        (resource_xml, out_dict) = self._get_resource_xml_with_links(req, item)
        if util.get_content_accept_type(req) == 'xml':
            return util.create_response('application/xml', resource_xml)
        else:
            # Parsing back xml to remove instance state attributes
            # in the object
            converted_dict = util.xml_to_dict(resource_xml)
            if converted_dict is None:
                converted_dict = {}
            resource_dict = {self._model_name: converted_dict}
            util.update_dict_using_xpath(resource_dict, out_dict)
            LOG.debug(_('Dict after conversion %s'
                      % str(resource_dict)))
            return util.create_response('application/json',
                    json.dumps(resource_dict))

    def get_all_by_filters(self, req, func):
        """
        Get all items from the resource interface with filters parsed from the
        request.
        :param req: webob request
        :param func: resource interface function taking parameters context,
        filters, sort_key and sort_dir
        :returns: all filtered items of the resource model type.
        """
        ctx = util.get_project_context(req)[0]
        filters, sort_key, sort_dir = self.get_search_options(req,
                                            getattr(healthnmonResourceModel,
                                                          self._model_name))
        try:
            return func(ctx, filters, sort_key, sort_dir)
        except sql_exc.DataError, e:
            LOG.error(_('Data value error %s ' % str(e)), exc_info=1)
            raise Invalid(message=_('Invalid parameter values'))

    def get_search_options(self, req, model):
        """ Get search options from WebOb request which can be
            input to xxx_get_all_by_filters DB APIs
            Arguments:
                req - WebOb request object
                model - Resource model object for which this API is invoked
            Returns:
                 tuple containing dictonary of filters, sort_key and sort direction
        """
        query_params = {}
        query_params.update(req.GET)

        for key in query_params:
            if(len(req.GET.getall(key)) > 1):
                query_params[key] = req.GET.getall(key)

        filters = {}
        # Parse ISO 8601 formatted changes-since input to epoch millisecs
        if 'changes-since' in query_params:
            try:
                parsed = timeutils.parse_isotime(query_params['changes-since'])
                utctimetuple = parsed.utctimetuple()
                epoch_ms = long(calendar.timegm(utctimetuple) * 1000L)
            except ValueError:
                msg = _('Invalid changes-since value')
                raise exc.HTTPBadRequest(explanation=msg)
            filters['changes-since'] = epoch_ms

        if 'deleted' in query_params:
                if query_params['deleted'].lower() == 'true':
                        filters['deleted'] = 'true'
                elif query_params['deleted'].lower() == 'false':
                        filters['deleted'] = 'false'
                else:
                        msg = _('Invalid deleted value')
                        raise exc.HTTPBadRequest(explanation=msg)

        # By default, dbs xxx_get_all_by_filters() will return deleted rows.
        # If an admin hasn't specified a 'deleted' search option, we need
        # to filter out deleted rows by setting the filter ourselves.
        # ... Unless 'changes-since' is specified, because 'changes-since'
        # should return recently deleted rows also.
        if 'deleted' not in query_params:
            if 'changes-since' not in query_params:
                # No 'changes-since', so we only want non-deleted rows
                filters['deleted'] = 'false'
        model_members = model.get_all_members()
        for key in query_params:
            if key in model_members:
                value = model_members[key]
                # For enum the value.data_type would be as [<Enumname>, xs:String]
                if (type(value.data_type) == ListType):
                    value.data_type = value.data_type[1]
                if not hasattr(healthnmonResourceModel, value.data_type):
                    filters[key] = query_params[key]
        sort_key = None
        sort_dir = DbConstants.ORDER_DESC
        if 'createEpoch' in model_members:
            sort_key = 'createEpoch'
            sort_dir = DbConstants.ORDER_DESC
        else:
            sort_key = 'id'
            sort_dir = DbConstants.ORDER_DESC

        return (filters, sort_key, sort_dir)

    def limited_by_marker(self, items, request, max_limit=FLAGS.osapi_max_limit):
        """
        Return a tuple with slice of items according to the requested marker
        and limit and a set of collection links

        :params items: resource item list
        :params request: webob request
        :params max_limit: maximum number of items to be returned
        :returns: (limited item list, collection links list) as a tuple
        """
        collection_links = []
        params = common.get_pagination_params(request)
        limit = params.get('limit', max_limit)
        marker = params.get('marker')
        limit = min(max_limit, limit)
        if limit == 0:
            return ([], [])
        start_index = 0
        if marker:
            start_index = -1
            for i, item in enumerate(items):
                #NOTE(siva): getter from generateDS
                if item.get_id() == marker:
                    start_index = i + 1
                    break
            if start_index < 0:
                msg = _('marker [%s] not found') % marker
                raise webob.exc.HTTPBadRequest(explanation=msg)
        range_end = start_index + limit
        prev_index = start_index - limit
        try:
            items[range_end]
            items[range_end - 1]
        except Exception:
            pass
        else:
            collection_links.append({
                    'rel': 'next',
                    'href': self._get_next_link(request,
                                        str(items[range_end - 1].get_id()), self._collection_name)
                })
        if prev_index > 0:
            collection_links.append({
                    'rel': 'previous',
                    'href': self._get_previous_link(request,
                                        str(items[prev_index - 1].get_id()), self._collection_name)
                })
        elif prev_index == 0:
            collection_links.append({
                    'rel': 'previous',
                    'href': self._get_previous_link(request, None, self._collection_name)
                })
        return (items[start_index:range_end], collection_links)

    def _get_previous_link(self, request, identifier, collection_name):
        """
        Return href string with proper limit and marker params. If identifier
        is not specified, no marker would be added.
        :params request: webob request
        :params identifier: unique identifier for the resource
        :returns: href string with limit and marker params.
        """
        params = request.params.copy()
        if identifier:
            params["marker"] = identifier
        elif "marker" in params:
            del params["marker"]
        prefix = self._update_link_prefix(request.application_url,
                                          FLAGS.osapi_compute_link_prefix)
        url = os.path.join(prefix,
                           request.environ["nova.context"].project_id,
                           collection_name)
        return "%s?%s" % (url, common.dict_to_query_str(params))

    #NOTE(siva): This method is overridden to retain filtered output.
    def _get_href_link(self, request, identifier, collection_name):
        """Return an href string pointing to this object."""
        prefix = self._update_link_prefix(request.application_url,
                                          FLAGS.osapi_compute_link_prefix)
        url = os.path.join(prefix,
                            request.environ["nova.context"].project_id,
                            collection_name,
                            str(identifier))
        if 'fields' in request.params:
            return "%s?%s" % (url,
                common.dict_to_query_str({'fields': request.params['fields']}))
        else:
            return url
