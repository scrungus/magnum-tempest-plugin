import fixtures

from oslo_log import log as logging
from oslo_utils import uuidutils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions
import testtools

from magnum_tempest_plugin.common import utils
from magnum_tempest_plugin.common import config
from magnum_tempest_plugin.common import datagen

from magnum_tempest_plugin.tests.api import base

from magnum_tempest_plugin.tests.api.v1 import test_cluster

import base64 

HEADERS = {'OpenStack-API-Version': 'container-infra latest',
           'Accept': 'application/json',
           'Content-Type': 'application/json'}

class ClusterAccessTest(test_cluster.ClusterTest): # fai.ClusterTest

    def __init__(self, *args, **kwargs):
        super(ClusterAccessTest, self).__init__(*args, **kwargs)
    
    @classmethod
    def setUpClass(cls):
        super(ClusterAccessTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(ClusterAccessTest, cls).tearDownClass()

    def setUp(self):
        super(ClusterAccessTest, self).setUp()

    def tearDown(self):
        super(ClusterAccessTest, self).tearDown()


    @testtools.testcase.attr('positive')
    @decorators.idempotent_id('f4c33092-7eeb-43d7-826e-bba16fd61e28')
    def test_create_cluster_and_get_kubeconfig(self):
        #cluster template set up by fai.ClusterTest
        #either provided in config or generated
        gen_model = datagen.valid_cluster_data(
            cluster_template_id=self.cluster_template.uuid, node_count=1)
        
        # test cluster create
        _, cluster_model = self._create_cluster(gen_model)
        self.assertNotIn('status', cluster_model)

        #print cluster details
        resp = self.cluster_client.get_cluster(cluster_model.uuid)
        print(resp)

        #template kubeconfig
        
        #generate csr and private key
        csr_sample = utils.generate_csr_and_key()

        #create request
        cert_data_model = datagen.cert_data(cluster_model.uuid,
                                            csr_data=csr_sample['csr'])

        #post request to magnum api, get CA cert and signed CSR back
        resp, cert_model = self.cert_client.post_cert(cert_data_model,
                                                      headers=HEADERS)
        #self.LOG.debug("cert resp: %s", resp)
        print("cert resp: %s", resp)

        cfg = ("apiVersion: v1\n"
                "clusters:\n"
                "- cluster:\n"
                "    certificate-authority-data: %(ca)s\n"
                "    server: %(api_address)s\n"
                "  name: %(name)s\n"
                "contexts:\n"
                "- context:\n"
                "    cluster: %(name)s\n"
                "    user: admin\n"
                "  name: default\n"
                "current-context: default\n"
                "kind: Config\n"
                "preferences: {}\n"
                "users:\n"
                "- name: admin\n"
                "  user:\n"
                "    client-certificate-data: %(cert)s\n"
                "    client-key-data: %(key)s\n"
                % {'name': cluster_model.name,
                    'api_address': cluster_model.api_address,
                    'key': base64.encode_as_text(csr_sample['key']),
                    'cert': base64.encode_as_text(cert_model['csr']),
                    'ca': base64.encode_as_text(cert_model['pem'])})

