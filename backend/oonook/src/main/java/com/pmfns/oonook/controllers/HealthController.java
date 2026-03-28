package com.pmfns.oonook.controllers;

import com.pmfns.oonook.services.AgentsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/health")
public class HealthController {

    private final AgentsService agentsService;

    @GetMapping
    public ResponseEntity<Map<String, Object>> health() {
        boolean agentsReachable = agentsService.isAgentsReachable();
        return ResponseEntity.ok(Map.of(
                "status", "ok",
                "agents_reachable", agentsReachable));
    }
}
