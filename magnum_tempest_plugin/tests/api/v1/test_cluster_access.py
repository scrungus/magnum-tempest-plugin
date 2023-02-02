import fixtures

from oslo_log import log as logging
from oslo_utils import uuidutils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions
import testtools

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

        #sign CA

        csr_sample = """-----BEGIN CERTIFICATE REQUEST-----
MIIByjCCATMCAQAwgYkxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlh
MRYwFAYDVQQHEw1Nb3VudGFpbiBWaWV3MRMwEQYDVQQKEwpHb29nbGUgSW5jMR8w
HQYDVQQLExZJbmZvcm1hdGlvbiBUZWNobm9sb2d5MRcwFQYDVQQDEw53d3cuZ29v
Z2xlLmNvbTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEApZtYJCHJ4VpVXHfV
IlstQTlO4qC03hjX+ZkPyvdYd1Q4+qbAeTwXmCUKYHThVRd5aXSqlPzyIBwieMZr
WFlRQddZ1IzXAlVRDWwAo60KecqeAXnnUK+5fXoTI/UgWshre8tJ+x/TMHaQKR/J
cIWPhqaQhsJuzZbvAdGA80BLxdMCAwEAAaAAMA0GCSqGSIb3DQEBBQUAA4GBAIhl
4PvFq+e7ipARgI5ZM+GZx6mpCz44DTo0JkwfRDf+BtrsaC0q68eTf2XhYOsq4fkH
Q0uA0aVog3f5iJxCa3Hp5gxbJQ6zV6kJ0TEsuaaOhEko9sdpCoPOnRBm2i/XRD2D
6iNh8f8z0ShGsFqjDgFHyF3o+lUyj+UC6H1QW7bn
-----END CERTIFICATE REQUEST-----
"""
        cert_data_model = datagen.cert_data(cluster_model.uuid,
                                            csr_data=csr_sample)
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
                   "    user: openstackuser\n"
                   "  name: openstackuser@kubernetes\n"
                   "current-context: openstackuser@kubernetes\n"
                   "kind: Config\n"
                   "preferences: {}\n"
                   "users:\n"
                   "- name: openstackuser\n"
                   "  user:\n"
                   "    exec:\n"
                   "      command: /bin/bash\n"
                   "      apiVersion: client.authentication.k8s.io/v1alpha1\n"
                   "      args:\n"
                   "      - -c\n"
                   "      - >\n"
                   "        if [ -z ${OS_TOKEN} ]; then\n"
                   "            echo 'Error: Missing OpenStack credential from environment variable $OS_TOKEN' > /dev/stderr\n"  # noqa
                   "            exit 1\n"
                   "        else\n"
                   "            echo '{ \"apiVersion\": \"client.authentication.k8s.io/v1alpha1\", \"kind\": \"ExecCredential\", \"status\": { \"token\": \"'\"${OS_TOKEN}\"'\"}}'\n"  # noqa
                   "        fi\n"
                   % {'name': cluster_model.name,
                      'api_address': cluster_model.api_address,
                      'ca': base64.encode_as_text(cert_model.pem)})

