# 03_c2.py
from utils import run

print("=== C2 Simulado ===")

run("docker run -d --name c2_zona6 --network zona6_red --ip 10.3.0.20 nginx")