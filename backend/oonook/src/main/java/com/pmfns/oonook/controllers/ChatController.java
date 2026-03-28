package com.pmfns.oonook.controllers;

import com.pmfns.oonook.models.ChatRequest;
import com.pmfns.oonook.models.ChatResponse;
import com.pmfns.oonook.services.AgentsService;

import lombok.RequiredArgsConstructor;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/chat")
public class ChatController {

    private final AgentsService agentsService;

    @PostMapping
    public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest request) {
        return agentsService.forwardChat(request);
    }
}
