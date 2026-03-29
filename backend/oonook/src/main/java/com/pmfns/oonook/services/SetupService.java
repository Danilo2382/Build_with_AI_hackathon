package com.pmfns.oonook.services;

import com.google.cloud.firestore.Firestore;
import com.pmfns.oonook.models.SetupRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class SetupService {

    private final Firestore firestore;

    public Mono<Boolean> saveSetup(SetupRequest request) {
        return Mono.fromCallable(() -> {
            String userId = request.userId();
            log.info("[Setup] saving for userId={} patientName={}", userId, request.patientName());

            // medication/data
            Map<String, Object> medicationData = new HashMap<>();
            medicationData.put("patient_name", request.patientName());
            medicationData.put("medications", request.medications());
            log.info("[Setup] writing medication: {}", medicationData);
            firestore.collection("agent_memory")
                    .document(userId)
                    .collection("medication")
                    .document("data")
                    .set(medicationData)
                    .get();
            log.info("[Setup] medication written OK");

            // people/data
            Map<String, Object> peopleData = new HashMap<>();
            peopleData.put("contacts", request.contacts());
            log.info("[Setup] writing people: {}", peopleData);
            firestore.collection("agent_memory")
                    .document(userId)
                    .collection("people")
                    .document("data")
                    .set(peopleData)
                    .get();
            log.info("[Setup] people written OK");

            // checkup/data
            Map<String, Object> checkupData = new HashMap<>();
            checkupData.put("patient_name", request.patientName());
            checkupData.put("appointments", request.appointments());
            log.info("[Setup] writing checkup: {}", checkupData);
            firestore.collection("agent_memory")
                    .document(userId)
                    .collection("checkup")
                    .document("data")
                    .set(checkupData)
                    .get();
            log.info("[Setup] checkup written OK");

            return true;
        });
    }
}
