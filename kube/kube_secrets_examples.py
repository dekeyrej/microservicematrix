""" usage examples for kube_secrets.py class/methods """
import kube

ks = kube.KubeSecrets(False)  # True for inside the cluster, False for outside the cluster
ks.status_msgs = True
ks.debug = False
# def delete_secret(namespace, secret_name):
# def create_secret(namespace, secret_name, data_name, secstring):
# def update_secret(namespace, secret_name, data_name, secstring):
# def read_secret(namespace, secret_name, data_name, data_is_json):

# with open('last_sha.txt', 'rt') as file:
#     secdata = file.read()
#     file.close()

ks.delete_secret(namespace='devops-tools',
                secret_name='last-jenkins-successful-build')

# ks.create_secret(namespace='devops-tools',
#                 secret_name='last-jenkins-successful-build',
#                 data_name='commit',
#                 secstring=secdata)

# status = ks.update_secret(namespace='devops-tools',
#                 secret_name='last-jenkins-successful-build',
#                 data_name='commit',
#                 secstring=secdata)

# secret = ks.read_secret(namespace='devops-tools',
#                         secret_name='last-jenkins-successful-build',
#                         data_name='commit',
#                         data_is_json=False)

# print(f"Last commit (secret) = '{secret}'")
