package com.pmfns.oonook.services;

import com.pmfns.oonook.models.Reminder;
import com.pmfns.oonook.repositories.ReminderRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class RemindersServiceImpl implements RemindersService {

    private final ReminderRepository reminderRepository;

    @Override
    public Mono<List<Reminder>> getReminders(String userId) {
        return reminderRepository.findAllByUserId(userId).collectList();
    }

    @Override
    public Mono<Boolean> confirmReminder(String userId, String reminderId) {
        return reminderRepository.findById(reminderId)
                .flatMap(reminder -> {
                    if (userId.equals(reminder.getUserId())) {
                        reminder.setStatus("confirmed");
                        return reminderRepository.save(reminder).thenReturn(true);
                    }
                    return Mono.just(false);
                })
                .defaultIfEmpty(false);
    }
}
