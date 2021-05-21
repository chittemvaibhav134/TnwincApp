package com.navex.keycloak.moonwatch;

import java.net.URI;
import java.util.Map;

import software.amazon.awssdk.auth.credentials.*;
import software.amazon.awssdk.auth.signer.Aws4Signer;
import software.amazon.awssdk.awscore.client.builder.AwsDefaultClientBuilder;
import software.amazon.awssdk.core.client.builder.SdkSyncClientBuilder;
import software.amazon.awssdk.core.client.config.SdkAdvancedClientOption;
import software.amazon.awssdk.core.client.config.SdkClientOption;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;

public class MoonwatchClientBuilder extends AwsDefaultClientBuilder<MoonwatchClientBuilder, MoonwatchClient>
        implements SdkSyncClientBuilder<MoonwatchClientBuilder, MoonwatchClient> {
    private final static String CRED_KEY_ID = "AWS_MW_ACCESS_KEY_ID", CRED_SECRET = "AWS_MW_SECRET_ACCESS_KEY";
    private String logContext;

    MoonwatchClientBuilder(String logContext, SessionProviderConfig config) {
        super();
        this.logContext = logContext;

        AwsCredentialsProvider creds;
        Map<String, String> env = System.getenv();
        if( env.containsKey(CRED_KEY_ID) ) {
            Logger.writeInfo(logContext, "Loading Moonwatch API credentials from the Environment.");
            creds = StaticCredentialsProvider.create(AwsBasicCredentials.create(env.get(CRED_KEY_ID), env.get(CRED_SECRET)));
        } else {
            Logger.writeInfo(logContext, "Loading Moonwatch API credentials from container session.");
            creds = DefaultCredentialsProvider.create();
        }

        this.setEndpointOverride(URI.create(config.moonwatchApiBase));
        this.setCredentialsProvider(creds);
        this.setRegion(Region.of(config.awsRegion));
        

        this.httpClientBuilder(UrlConnectionHttpClient.builder());
        this.clientConfiguration.option(SdkAdvancedClientOption.SIGNER, Aws4Signer.create());
        this.clientConfiguration.option(SdkClientOption.SIGNER_OVERRIDDEN, true);
    }

    @Override
    protected String serviceEndpointPrefix() {
        return "";
    }

    @Override
    protected String signingName() {
        return "execute-api";
    }

    @Override
    protected String serviceName() {
        return "Moonwatch KeyCloak SPI";
    }

    @Override
    protected MoonwatchClient buildClient() {
        var config = this.syncClientConfiguration();
        return new MoonwatchClient(logContext, config);
    }

}
