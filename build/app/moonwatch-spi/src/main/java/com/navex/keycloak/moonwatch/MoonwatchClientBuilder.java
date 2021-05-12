package com.navex.keycloak.moonwatch;

import java.net.URI;

import com.amazonaws.Protocol;
import com.amazonaws.annotation.NotThreadSafe;
import com.amazonaws.client.AwsSyncClientParams;
import com.amazonaws.opensdk.internal.config.ApiGatewayClientConfigurationFactory;
import com.amazonaws.opensdk.protect.client.SdkSyncClientBuilder;
import com.amazonaws.util.RuntimeHttpUtils;

@NotThreadSafe
public class MoonwatchClientBuilder extends SdkSyncClientBuilder<MoonwatchClientBuilder, MoonwatchClient> {
    private final URI configEndpoint;
    private final String configRegion;


    MoonwatchClientBuilder(SessionProviderConfig config) {
        super(new ApiGatewayClientConfigurationFactory());

        this.configRegion = config.awsRegion;
        this.configEndpoint = RuntimeHttpUtils.toUri(config.moonwatchApiBase, Protocol.HTTPS);
    }

    @Override
    protected MoonwatchClient build(AwsSyncClientParams clientParams) {
        return new MoonwatchClient(clientParams);
    }

    @Override
    protected URI defaultEndpoint() {
        return configEndpoint;
    }

    @Override
    protected String defaultRegion() {
        return configRegion;
    }


}
