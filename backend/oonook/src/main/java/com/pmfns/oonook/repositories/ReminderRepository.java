package com.pmfns.oonook.repositories;

import com.google.cloud.spring.data.firestore.FirestoreReactiveRepository;
import com.pmfns.oonook.models.Reminder;
import reactor.core.publisher.Flux;

public interface ReminderRepository extends FirestoreReactiveRepository<Reminder> {
    Flux<Reminder> findAllByUserId(String userId);
}
