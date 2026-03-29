package com.pmfns.oonook.models;

import com.fasterxml.jackson.annotation.JsonProperty;

public record VoiceChatRequest(
        @JsonProperty("user_id") String userId,
        @JsonProperty("audio_base64") String audioBase64,
        @JsonProperty("mime_type") String mimeType
) {
}
