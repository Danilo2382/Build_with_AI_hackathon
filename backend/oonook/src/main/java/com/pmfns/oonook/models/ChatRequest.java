package com.pmfns.oonook.models;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ChatRequest(
        @JsonProperty("user_id") String userId,
        @JsonProperty("message") String message,
        @JsonProperty("audio_base64") String audioBase64
) {
}
