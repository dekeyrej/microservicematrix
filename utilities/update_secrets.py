""" utility to update kubernetes secret with content of local secrets.json """
import kube

kks = kube.KubeSecrets(False)

with open('secrets.json', 'rt', encoding='utf-8') as file:
    secdata = file.read()
    file.close()

kks.update_secret("default", "matrix-secrets", "secrets.json", secdata)
