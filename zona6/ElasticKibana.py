from utils import run

print("=== ELK Stack ===")

run("docker run -d --name elastic_zona6 \
--network zona6_red \
--ip 10.3.0.40 \
-e discovery.type=single-node \
-p 9200:9200 \
docker.elastic.co/elasticsearch/elasticsearch:8.5.0")

run("docker run -d --name kibana_zona6 \
--network zona6_red \
--ip 10.3.0.41 \
-p 5602:5601 \
docker.elastic.co/kibana/kibana:8.5.0")