Remove-Item -Recurse -Force .\import\

New-Item -ItemType Directory .\import\

docker exec -it keycloak-app /opt/jboss/tools/docker-entrypoint.sh '-Djboss.socket.binding.port-offset=100 -Dkeycloak.migration.action=export -Dkeycloak.migration.provider=dir -Dkeycloak.migration.dir=/import'
