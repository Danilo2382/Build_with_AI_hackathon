package com.pmfns.oonook.repositories;

import com.google.cloud.spring.data.firestore.FirestoreReactiveRepository;
import com.pmfns.oonook.models.Contact;
import reactor.core.publisher.Flux;

public interface ContactRepository extends FirestoreReactiveRepository<Contact> {
    Flux<Contact> findAllByUserId(String userId);
}
