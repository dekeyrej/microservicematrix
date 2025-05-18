import json
from pprint import pprint
import kube

ks = kube.KubeSecrets(False)  # True for inside the cluster, False for outside the cluster
ks.status_msgs = False
ks.debug = False

with open('events.json', 'r') as f:
    values = json.load(f)
# pprint(values, width=120)

cm_name = 'matrix-events'
namespace = 'default'
data = {"events.json" : json.dumps(values)}

ks.update_map(namespace, cm_name, data)

events = ks.read_map_data(namespace, cm_name, 'events.json', True)

events2 = ks.read_secret(namespace, 'matrix-events', 'events', True)

pprint(events, width=120)
pprint(events2, width=120)

if events == events2:
    print("Events match")