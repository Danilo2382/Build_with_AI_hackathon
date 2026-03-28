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

    // Regenerate reminders for demo_user every 6 hours
    @Scheduled(cron = "0 0 */6 * * *")
    public void generateReminders() {
        log.info("Generating reminders for demo_user");
        try {
            agentsService.generateReminders("demo_user");
            log.info("Reminders generated successfully");
        } catch (Exception e) {
            log.error("Failed to generate reminders: {}", e.getMessage());
        }
    }
}
