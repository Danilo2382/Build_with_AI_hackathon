package com.pmfns.oonook.controllers;

import com.pmfns.oonook.models.Reminder;
import com.pmfns.oonook.services.RemindersService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/reminders")
@RequiredArgsConstructor
public class RemindersController {

    private final RemindersService remindersService;

    @GetMapping
    public Mono<ResponseEntity<Map<String, List<Reminder>>>> getReminders(@RequestParam("user_id") String userId) {
        return remindersService.getReminders(userId)
                .map(reminders -> ResponseEntity.ok(Map.of("reminders", reminders)));
    }

    @PostMapping("/confirm")
    public Mono<ResponseEntity<Map<String, Object>>> confirmReminder(@RequestBody Map<String, String> request) {
        String userId = request.get("user_id");
        String reminderId = request.get("reminder_id");
        
        return remindersService.confirmReminder(userId, reminderId)
                .map(confirmed -> {
                    if (confirmed) {
                        return ResponseEntity.ok(Map.of(
                                "confirmed", true,
                                "response", "Great, I marked your reminder as taken!"
                        ));
                    } else {
                        return ResponseEntity.status(404).body(Map.of(
                                "confirmed", false,
                                "response", "Reminder not found or user mismatch."
                        ));
                    }
                });
    }
}
