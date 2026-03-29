package com.pmfns.oonook.services;

import com.pmfns.oonook.models.ChatRequest;
import com.pmfns.oonook.models.ChatResponse;
import com.pmfns.oonook.models.VideoRequest;
import com.pmfns.oonook.models.VisionRequest;
import com.pmfns.oonook.models.VoiceChatRequest;

import java.util.Map;

import lombok.RequiredArgsConstructor;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
@RequiredArgsConstructor
public class AgentsService {

    private final RestClient restClient;

    public boolean isAgentsReachable() {
        try {
            ResponseEntity<Void> response = restClient.get()
                    .uri("/health")
                    .retrieve()
                    .toBodilessEntity();
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            return false;
        }
    }

    public ResponseEntity<ChatResponse> forwardChat(ChatRequest request) {
        Map<String, Object> body = new java.util.HashMap<>();
        body.put("user_id", request.userId());
        if (request.message() != null) body.put("message", request.message());
        if (request.audioBase64() != null) body.put("audio_base64", request.audioBase64());
        return restClient.post()
                .uri("/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public ResponseEntity<ChatResponse> forwardVoiceChat(VoiceChatRequest request) {
        Map<String, Object> body = new java.util.HashMap<>();
        body.put("user_id", request.userId());
        body.put("audio_base64", request.audioBase64());
        if (request.mimeType() != null) body.put("mime_type", request.mimeType());
        return restClient.post()
                .uri("/chat/voice")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public ResponseEntity<ChatResponse> forwardVision(VisionRequest request) {
        return restClient.post()
                .uri("/vision/image")
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of("user_id", request.userId(), "image_base64", request.imageBase64()))
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public ResponseEntity<ChatResponse> forwardVideo(VideoRequest request) {
        return restClient.post()
                .uri("/vision/video")
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of("user_id", request.userId(), "video_base64", request.videoBase64()))
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public void generateReminders(String userId) {
        restClient.post()
                .uri("/reminders/generate")
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of("user_id", userId))
                .retrieve()
                .toBodilessEntity();
    }
}
