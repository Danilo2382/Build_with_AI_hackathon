package com.pmfns.oonook.controllers;

import com.pmfns.oonook.models.SetupRequest;
import com.pmfns.oonook.services.SetupService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/setup")
public class SetupController {

    private final SetupService setupService;

    @PostMapping
    public Mono<ResponseEntity<Map<String, Boolean>>> setup(@RequestBody SetupRequest request) {
        return setupService.saveSetup(request)
                .map(saved -> ResponseEntity.ok(Map.of("saved", saved)));
    }
}
