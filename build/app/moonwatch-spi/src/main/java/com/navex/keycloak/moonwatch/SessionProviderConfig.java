package com.navex.keycloak.moonwatch;

import java.util.Hashtable;
import java.util.Map;
import java.util.Stack;

import com.launchdarkly.sdk.*;
import com.launchdarkly.sdk.server.*;

public class SessionProviderConfig {
    private static String togglePrefix = "TOGGLE_";

    public String awsRegion;
    public String moonwatchApiBase;
    LDClient ldClient;
    Hashtable<String,Boolean> localToggles;

    public SessionProviderConfig() {
        super();
        localToggles = new Hashtable<String,Boolean>();

        Map<String, String> env = System.getenv();
        for (String envKey : env.keySet()) {
            if( envKey.startsWith(togglePrefix) ) {
                String key = envKey.substring(togglePrefix.length());
                String value = env.get(envKey);
                System.out.println("Found local toggle " + key + " with value " + value);
                localToggles.put(key.toLowerCase(), Boolean.parseBoolean(value));
            }
        }
    }

    public void setLaunchDarklyClient(LDClient client) {
        ldClient = client;
    }

    public boolean isToggleEnabled(String toggleName, String clientKey, boolean defaultValue) {
        if( localToggles.containsKey(toggleName.toLowerCase()) || ldClient == null) {
            return localToggles.getOrDefault(toggleName.toLowerCase(), defaultValue);
        }
        try {
            return GetToggleState(toggleName, new LDUser(clientKey), defaultValue, null);
        }
        catch(Exception ex) {
            return defaultValue;
        }
    }

    /**
     * 
     * @param toggleName
     * @param user
     * @param defaultValue
     * @param flagStack
     * @return
     */
    private boolean GetToggleState( String toggleName, LDUser user, boolean defaultValue, Stack<String> flagStack ) throws Exception {
        if( flagStack != null && flagStack.contains( toggleName ) ) {
            throw new Exception( "Infinite loop detected for " + toggleName );
        }
        
        boolean result = defaultValue;

        EvaluationDetail<String> toggleStringResult = ldClient.stringVariationDetail( toggleName, user, String.valueOf(defaultValue) );
        EvaluationReason resultReason = toggleStringResult.getReason();

        if( resultReason.getKind() == EvaluationReason.Kind.ERROR  &&
            resultReason.getErrorKind() == EvaluationReason.ErrorKind.WRONG_TYPE )
        {
            EvaluationDetail<Boolean> resultDetails = ldClient.boolVariationDetail( toggleName, user, defaultValue );
            result = resultDetails.getValue();
        }
        else if( resultReason.getKind() == EvaluationReason.Kind.ERROR )
        {
            throw new Exception( "toggle: " + toggleName + " not found " + resultReason.toString() );
        }
        else if( !"true".equalsIgnoreCase(toggleStringResult.getValue()) && !"false".equalsIgnoreCase(toggleStringResult.getValue()) )
        {
            if( flagStack == null ) {
                flagStack = new Stack<String>();
            }
            flagStack.push( toggleName );
            result = GetToggleState( toggleStringResult.getValue(), user, defaultValue, flagStack );
        } else {
            result = "true".equalsIgnoreCase(toggleStringResult.getValue());
        }

        return result;
    }
}
