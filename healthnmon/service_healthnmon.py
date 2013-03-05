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
import random
from nova.service import Service
from nova import version
from nova import utils
from nova import context
from nova import exception
from nova.openstack.common import rpc
from nova import db
from healthnmon import log

LOG = log.getLogger(__name__)


class HealthnmonService(Service):

    def start(self):
        vcs_string = version.version_string_with_package()
        LOG.audit(_('Starting %(topic)s node (version %(vcs_string)s)'),
                  {'topic': self.topic, 'vcs_string': vcs_string})
        self.manager.init_host()
        self.model_disconnected = False
        ctxt = context.get_admin_context()
        try:
            service_ref = db.service_get_by_args(ctxt,
                                                 self.host,
                                                 self.binary)
            self.service_id = service_ref['id']
        except exception.NotFound:
            self._create_service_ref(ctxt)

        if self.backdoor_port is not None:
            self.manager.backdoor_port = self.backdoor_port

        self.conn = rpc.create_connection(new=True)
        LOG.debug(_("Creating Consumer connection for Service %s") %
                  self.topic)

        self.manager.pre_start_hook(rpc_connection=self.conn)

        rpc_dispatcher = self.manager.create_rpc_dispatcher()

        # Share this same connection for these Consumers
        self.conn.create_consumer(self.topic, rpc_dispatcher, fanout=False)

        node_topic = '%s.%s' % (self.topic, self.host)
        self.conn.create_consumer(node_topic, rpc_dispatcher, fanout=False)

        self.conn.create_consumer(self.topic, rpc_dispatcher, fanout=True)

        # Consume from all consumers in a thread
        self.conn.consume_in_thread()

        self.manager.post_start_hook()

        pulse = self.servicegroup_api.join(self.host, self.topic, self)
        if pulse:
            self.timers.append(pulse)

        if self.periodic_enable:
            if self.periodic_fuzzy_delay:
                initial_delay = random.randint(0, self.periodic_fuzzy_delay)
            else:
                initial_delay = None

            periodic = utils.DynamicLoopingCall(self.periodic_tasks)
            periodic.start(initial_delay=initial_delay,
                           periodic_interval_max=self.periodic_interval_max)
            self.timers.append(periodic)
