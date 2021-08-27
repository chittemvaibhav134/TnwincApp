FROM jboss/keycloak:15.0.2 AS base

FROM base as newrelic
WORKDIR /nr
USER root
RUN microdnf install -y unzip && microdnf clean all
RUN curl -O https://download.newrelic.com/newrelic/java-agent/newrelic-agent/current/newrelic-java.zip
RUN unzip newrelic-java.zip -d /nr

FROM maven:3.8.1-openjdk-11 AS moonwatch-build
WORKDIR /src
COPY "./moonwatch-spi/pom.xml" "./"
RUN mvn clean dependency:resolve dependency:resolve-plugins package
COPY ./moonwatch-spi .
RUN mvn clean package assembly:single

FROM base AS final
ENV NEW_RELIC_BROWSER_MONITORING_AUTO_INSTRUMENT false
ENV NEW_RELIC_LOG_LEVEL off
USER 1000
COPY --chown=jboss:root fs /
RUN chmod +x /opt/jboss/tools/start.sh && chmod +x /opt/jboss/startup-scripts/*.sh
COPY --from=newrelic --chown=root:root /nr /opt
COPY --from=moonwatch-build --chown=jboss:root \
    /src//target/moonwatch-session-spi.jar \
    /opt/jboss/keycloak/standalone/deployments/moonwatch-session-spi.jar
ENTRYPOINT /opt/jboss/tools/start.sh