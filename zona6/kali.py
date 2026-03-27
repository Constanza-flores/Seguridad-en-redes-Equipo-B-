
from utils import run

print("=== Kali Linux ===")

run("docker run -dit --name kali_zona6 --network zona6_red --ip 10.3.0.10 kalilinux/kali-rolling /bin/bash")

run("docker exec kali_zona6 apt update")
run("docker exec kali_zona6 apt install -y nmap curl net-tools")