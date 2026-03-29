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
        return reminderRepository.findAllByUserId(userId)
                .collectList()
                .map(list -> {
                    list.sort((a, b) -> {
                        boolean aConfirmed = "confirmed".equals(a.getStatus());
                        boolean bConfirmed = "confirmed".equals(b.getStatus());
                        if (aConfirmed != bConfirmed) return aConfirmed ? 1 : -1;
                        String aTime = a.getTime() != null ? a.getTime() : "";
                        String bTime = b.getTime() != null ? b.getTime() : "";
                        return aTime.compareTo(bTime);
                    });
                    return list;
                });
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

    @Override
    public Mono<Boolean> deleteReminder(String userId, String reminderId) {
        return reminderRepository.findById(reminderId)
                .flatMap(reminder -> {
                    if (userId.equals(reminder.getUserId())) {
                        return reminderRepository.delete(reminder).thenReturn(true);
                    }
                    return Mono.just(false);
                })
                .defaultIfEmpty(false);
    }
}
