FROM jboss/keycloak:8.0.2
COPY --chown=jboss:root fs /
RUN chmod +x /opt/jboss/tools/start.sh
ENTRYPOINT /opt/jboss/tools/start.sh