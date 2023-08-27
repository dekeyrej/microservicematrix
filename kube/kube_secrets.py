"""
Set of routines for manipulating kubernetes secrets either from inside the cluster,
or from outside the cluster - iff you have a valid ~./kube/config file
"""
import json
import base64
from kubernetes import client, config

class KubeSecrets:
    """ class definition for kubernetes secret routines """
    def __init__(self, in_kube = True):
        """ in_kube = True to read from inside the cluster, or False to read from outside """
        if in_kube:
            config.incluster_config.load_incluster_config()
        else:
            config.load_kube_config()
        self.api_instance = client.CoreV1Api()
        self.status_msgs  = False
        self.debug        = False
        self.pretty       = 'true'
        self.dry_run      = None

    def delete_secret(self, namespace, secret_name):
        """ routine to delete a namespaced secret """
        try:
            api_response = self.api_instance.read_namespaced_secret(secret_name, namespace)
            if self.debug: print(api_response)
            api_response = self.api_instance.delete_namespaced_secret(secret_name, namespace,
                                                                      pretty=self.pretty)
            if self.debug: print(api_response)
            if self.status_msgs: print(f'Secret "{secret_name}" in namespace'\
                                       f' "{namespace}" deleted.')
            return 0
        except client.exceptions.ApiException as apiex:
            if self.debug: print(apiex)
            print(f'Secret "{secret_name}" in namespace "{namespace}" not found.')
            return 1

    def create_secret(self, namespace, secret_name, data_name, secstring):
        """ routine to create a namespaced secret with a string as the input """
        body = client.V1Secret()
        body.api_version = 'v1'
        body.data = {data_name: base64.b64encode(secstring.encode()).decode()}
        body.kind = 'Secret'
        body.metadata = {'name': secret_name}
        body.type = 'Opaque'
        try:
            api_response = self.api_instance.create_namespaced_secret(namespace=namespace,
                                                                      body=body,
                                                                      pretty=self.pretty,
                                                                      dry_run=self.dry_run)
            if self.debug: print(api_response)
            if self.status_msgs: print(f'Secret "{secret_name}" in namespace'\
                                       f' "{namespace}" created.')
            return 0
        except client.exceptions.ApiException as apiex:
            if self.debug: print(apiex)
            return -1

    def read_secret(self, namespace, secret_name, data_name, data_is_json):
        """ routine to read an existing kubernetes secret.
            returns a string if data_is_json = False, or
            returns a dict/list if data_is_json = True  """
        try:
            api_response = self.api_instance.read_namespaced_secret(secret_name, namespace)
            if self.debug: print(api_response)
            if data_is_json:
                secrets = json.loads(base64.b64decode(api_response.data[data_name]).decode('utf-8'))
                if self.status_msgs: print(f'Secret "{secret_name}" in namespace'\
                                           f' "{namespace}.{data_name}" is:')
                if self.status_msgs: print(json.dumps(secrets, indent=2))
                return secrets
            secret = base64.b64decode(api_response.data[data_name]).decode('utf-8')
            if self.status_msgs: print(f'Secret "{secret_name}" in namespace'\
                                       f' "{namespace}.{data_name}" is: "{secret}"')
            return secret
        except client.exceptions.ApiException as apiex:
            if self.debug: print(apiex)
            return -1

    def update_secret(self, namespace, secret_name, data_name, secstring):
        """ simple concatenation of deleting an existing secret and 
        replacing it with a new value """
        retval = self.delete_secret(namespace, secret_name)
        if retval >= 0:
            retval = self.create_secret(namespace, secret_name, data_name, secstring)
        return retval
