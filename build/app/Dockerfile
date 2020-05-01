FROM jboss/keycloak:8.0.2
USER root
RUN microdnf install -y unzip && microdnf clean all
RUN curl -O https://download.newrelic.com/newrelic/java-agent/newrelic-agent/current/newrelic-java.zip
RUN unzip newrelic-java.zip -d /opt
USER 1000
ENV NEW_RELIC_BROWSER_MONITORING_AUTO_INSTRUMENT false
ENV NEW_RELIC_LOG_LEVEL off
COPY --chown=jboss:root fs /
RUN chmod +x /opt/jboss/tools/start.sh
ENTRYPOINT /opt/jboss/tools/start.sh