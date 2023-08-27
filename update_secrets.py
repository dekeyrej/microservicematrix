import kube

ks = kube.kube_secrets(False)

with open('secrets.json', 'rt') as file:
    secdata = file.read()
    file.close()

ks.update_secret("default", "matrix-secrets", "secrets.json", secdata)