package com.navex.keycloak.moonwatch;

import java.io.InputStream;

import software.amazon.awssdk.core.util.json.JacksonUtils;
import software.amazon.awssdk.http.ContentStreamProvider;
import software.amazon.awssdk.utils.StringInputStream;

public class JsonContentStream implements ContentStreamProvider {
    StringInputStream stream;

    public JsonContentStream(Object obj) {
        stream = new StringInputStream(JacksonUtils.toJsonString(obj));
    }

    @Override
    public InputStream newStream() {
        stream.reset();
        return stream;
    }
}
