package com.pmfns.oonook.services;

import com.pmfns.oonook.models.Reminder;
import reactor.core.publisher.Mono;
import java.util.List;

public interface RemindersService {
    Mono<List<Reminder>> getReminders(String userId);
    Mono<Boolean> confirmReminder(String userId, String reminderId);
}
