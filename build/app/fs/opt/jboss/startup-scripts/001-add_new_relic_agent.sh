
if ! $NEW_RELIC_AGENT_ENABLED; then
    echo "NEW_RELIC_AGENT_ENABLED was not set to true; skipping java agent JAVA_OPT"
else
    JAVA_AGENT='-javaagent:/opt/newrelic/newrelic.jar'
    echo "NEW_RELIC_AGENT_ENABLED set to true; adding $JAVA_AGENT to JAVA_OPTS..."
    echo "JAVA_OPTS=\"\$JAVA_OPTS $JAVA_AGENT\"" >> $JBOSS_HOME/bin/standalone.conf
fi