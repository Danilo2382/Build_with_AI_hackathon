package com.pmfns.oonook.services;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class RemindersScheduler {

    private final AgentsService agentsService;

    // Regenerate reminders for nikola every 6 hours
    @Scheduled(cron = "0 0 */6 * * *")
    public void generateReminders() {
        log.info("Generating reminders for nikola");
        try {
            agentsService.generateReminders("nikola");
            log.info("Reminders generated successfully");
        } catch (Exception e) {
            log.error("Failed to generate reminders: {}", e.getMessage());
        }
    }
}
