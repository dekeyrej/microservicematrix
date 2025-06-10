secretcfg = {
    "SOURCE": "KUBEVAULT",
    "kube_config": None,
    "service_account": "default",
    "namespace": "default",
    "vault_url": "https://192.168.86.9:8200",
    "role": "demo",
    "ca_cert": True  # or path to CA cert file
}
####
secretdef = {
    "transit_key": "aes256-key",
    "namespace": "default", 
    "secret_name": "matrix-secrets",
    "read_type": "SECRET",
    "secret_key": "secrets.json"
}