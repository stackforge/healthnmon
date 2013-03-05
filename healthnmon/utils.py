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

import time
from lxml import etree
from healthnmon.resourcemodel import resourcemodel_diff
from nova import utils
from nova.openstack.common import cfg
from nova.openstack.common import timeutils
from healthnmon import log

# including instances_path defined in nova.compute.manager
# in order to create nova-storage-pool
CONF = cfg.CONF
CONF.import_opt('instances_path', 'nova.compute.manager')
LOG = log.getLogger(__name__)


def get_current_epoch_ms():
    return long(time.time() * 1000)


def getFlagByKey(key):
    """ Returns the value of the flag queried based on key"""
    CONF = cfg.CONF
    return CONF.get(key)


def is_service_alive(updated_at, created_at):
    delta = timeutils.utcnow() - (updated_at or created_at)
    return abs(utils.total_seconds(delta)) <= CONF.service_down_time


class XMLUtils:

    ''' Utils class to do extract the attributes and
    values out of the libvirt XML '''

    def __init__(self):
        pass

    def parseXML(self, xml, path, namespaces=None):
        """ Get element text from the matching xpath elements. If there
            is only one element, its text is returned instead.
            if xml uses namespaces, corresponding prefix mapping needs to
            be defined in namespaces. Eg:
            namespaces: { 'a':'http://namespace'}. Empty namespace prefixes
            are not supported in xpath.

        """
        node_list = []
        try:
            root = etree.fromstring(xml,
                                    parser=etree.XMLParser(
                                        remove_blank_text=True))
            nodes = root.xpath(
                path, smart_strings=False, namespaces=namespaces)
            if nodes is None or len(nodes) == 0:
                return None
            elif len(nodes) == 1:
                return nodes[0].text
            for node in nodes:
                node_list.append(node.text)
        except Exception:
            LOG.error(_("Error parsing xml with path:" + path), exc_info=1)
        return node_list

    def parseXMLAttributes(
        self,
        xml,
        path,
        attribute,
        all_matches=False,
        namespaces=None
    ):
        """ Fetches the attribute from the first element matched.
        If all_matches is enabled, gets a list of attribute values
        for all elements matched.
        When all_matches is False, if first element matched doesn't
        contain the attribute, returns None.
            if xml uses namespaces, corresponding prefix mapping needs to
            be defined in namespaces. Eg:
            namespaces: { 'a':'http://namespace'}. Empty namespace prefixes
            are not supported in xpath.

        """
        try:
            root = etree.fromstring(xml,
                                    parser=etree.XMLParser(
                                        remove_blank_text=True))
            nodes = root.xpath(
                path, smart_strings=False, namespaces=namespaces)
            if (nodes is not None) and (len(nodes) > 0):
                if all_matches is False:
                    return nodes[0].get(attribute, None)
                # all_matches is True. Return list.
                attr_values = []
                for node in nodes:
                    if node.get(attribute, None) is not None:
                        attr_values.append(node.get(attribute))
                return attr_values
        except Exception:
            LOG.error(_("Error parsing xml with path:" + path), exc_info=1)
        return None

    def getNodeXML(self, xml, path, namespaces=None):
        """ Return list of xml strings matching the object nodes
            if xml uses namespaces, corresponding prefix mapping needs to
            be defined in namespaces. Eg:
            namespaces: { 'a':'http://namespace'}. Empty namespace prefixes
            are not supported in xpath.
        """
        node_list = []
        try:
            root = etree.fromstring(xml,
                                    parser=etree.XMLParser(
                                        remove_blank_text=True))
            nodes = root.xpath(
                path, smart_strings=False, namespaces=namespaces)
            if len(nodes) == 0:
                return node_list
            for node in nodes:
                node_list.append(etree.tostring(node, encoding='UTF-8'))
        except Exception:
            LOG.error(_("Error parsing xml with path:" + path), exc_info=1)
        return node_list

    def getdiff(self, oldObject, newobject):
        """ Calculate the diff between two resource model objects

            Returns: A two element tuple.
                First element : True if there is a change else False
                Second element : None if the objects are same.
                Else a dictionary of differences
        """

        if oldObject is None:
            return (True, None)
        diff = resourcemodel_diff.ResourceModelDiff(oldObject,
                                                    newobject)
        diff_res = diff.diff_resourcemodel()
        if len(diff_res) > 0:
            return (True, diff_res)
        else:
            return (False, None)

    def getDeletionList(self, oldList, newList):
        deletion_list = []
        for item in oldList:
            if not item in newList:
                deletion_list.append(item)
        return deletion_list

    def log_error(self, exception):
        """Something went wrong. Check to see if compute_node should be
           marked as offline."""

        LOG.error(_('Exception Occurred %s ') % exception)

    def is_profile_in_list(self, ip_profile, ip_profile_list):
        """
        Check if ip_profile exist in the list-- does not check if profiles
        are None.
        :param ip_profile: Profile to be checked for
        :param ip_profile_list: list of ip profiles.
        """
        for prof in ip_profile_list:
            if prof.get_ipAddress() == ip_profile.get_ipAddress() and   \
                    prof.get_hostname() == ip_profile.get_hostname():
                return True
        return False
