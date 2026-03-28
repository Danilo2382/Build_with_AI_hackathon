package com.pmfns.oonook.services;

import com.pmfns.oonook.models.ChatRequest;
import com.pmfns.oonook.models.ChatResponse;
import com.pmfns.oonook.models.VideoRequest;
import com.pmfns.oonook.models.VisionRequest;

import lombok.RequiredArgsConstructor;

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
        return restClient.post()
                .uri("/chat")
                .body(request)
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public ResponseEntity<ChatResponse> forwardVision(VisionRequest request) {
        return restClient.post()
                .uri("/vision")
                .body(request)
                .retrieve()
                .toEntity(ChatResponse.class);
    }

    public ResponseEntity<ChatResponse> forwardVideo(VideoRequest request) {
        return restClient.post()
                .uri("/video")
                .body(request)
                .retrieve()
                .toEntity(ChatResponse.class);
    }
}
