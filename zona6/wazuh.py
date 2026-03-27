# 04_wazuh.py
from utils import run

print("=== Wazuh ===")

run("docker run -d --name wazuh_zona6 \
--network zona6_red \
--ip 10.3.0.30 \
-p 5601:5601 \
wazuh/wazuh-manager")