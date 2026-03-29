package com.pmfns.oonook.models;

import com.fasterxml.jackson.annotation.JsonProperty;

public record VisionRequest(
        @JsonProperty("user_id") String userId,
        @JsonProperty("image_base64") String imageBase64,
        @JsonProperty("prompt") String prompt
) {
}
