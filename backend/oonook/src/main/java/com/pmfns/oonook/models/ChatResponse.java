package com.pmfns.oonook.models;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ChatResponse(
        String response,
        String agent,
        Media media,
        @JsonProperty("audio_base64") String audioBase64
) {

    public record Media(String type, String url) {
    }
}
