package com.pmfns.oonook.services;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.pmfns.oonook.models.ChatRequest;
import com.pmfns.oonook.models.ChatResponse;
import com.pmfns.oonook.models.VideoRequest;
import com.pmfns.oonook.models.VisionRequest;

import lombok.RequiredArgsConstructor;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
@RequiredArgsConstructor
public class AgentsService {

    private final RestClient restClient;

    private record ChatPayload(
            @JsonProperty("user_id") String userId,
            @JsonProperty("audio_base64") String audioBase64) {}

    private record VisionPayload(
            @JsonProperty("user_id") String userId,
            @JsonProperty("image_base64") String imageBase64) {}

    private record VideoPayload(
            @JsonProperty("user_id") String userId,
            @JsonProperty("video_base64") String videoBase64) {}

    private record RemindersPayload(
            @JsonProperty("user_id") String userId) {}

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
        return restClient.post()
                .uri("/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .body(new ChatPayload(request.userId(), request.audioBase64()))
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public ResponseEntity<ChatResponse> forwardVision(VisionRequest request) {
        return restClient.post()
                .uri("/vision/image")
                .contentType(MediaType.APPLICATION_JSON)
                .body(new VisionPayload(request.userId(), request.imageBase64()))
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public ResponseEntity<ChatResponse> forwardVideo(VideoRequest request) {
        return restClient.post()
                .uri("/vision/video")
                .contentType(MediaType.APPLICATION_JSON)
                .body(new VideoPayload(request.userId(), request.videoBase64()))
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public void generateReminders(String userId) {
        restClient.post()
                .uri("/reminders/generate")
                .contentType(MediaType.APPLICATION_JSON)
                .body(new RemindersPayload(userId))
                .retrieve()
                .toBodilessEntity();
    }
}
