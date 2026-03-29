package com.pmfns.oonook.models;

import com.fasterxml.jackson.annotation.JsonProperty;

public record VideoRequest(
        @JsonProperty("user_id") String userId,
        @JsonProperty("video_base64") String videoBase64
) {
}
