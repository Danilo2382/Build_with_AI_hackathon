package com.pmfns.oonook.controllers;

import com.pmfns.oonook.models.ChatResponse;
import com.pmfns.oonook.models.VideoRequest;
import com.pmfns.oonook.models.VisionRequest;
import com.pmfns.oonook.services.AgentsService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping
public class VisionController {

    private final AgentsService agentsService;

    public VisionController(AgentsService agentsService) {
        this.agentsService = agentsService;
    }

    @PostMapping("/vision")
    public ResponseEntity<ChatResponse> vision(@RequestBody VisionRequest request) {
        return agentsService.forwardVision(request);
    }

    @PostMapping("/video")
    public ResponseEntity<ChatResponse> video(@RequestBody VideoRequest request) {
        return agentsService.forwardVideo(request);
    }
}
