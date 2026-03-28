package com.pmfns.oonook.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class RestClientConfig {

    @Value("${AGENTS_URL:http://localhost:8000}")
    private String agentsUrl;

    @Bean
    public RestClient agentsRestClient() {
        return RestClient.builder()
                .baseUrl(agentsUrl)
                .build();
    }
}
