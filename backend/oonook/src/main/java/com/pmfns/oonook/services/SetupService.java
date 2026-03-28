package com.pmfns.oonook.services;

import com.google.cloud.firestore.Firestore;
import com.pmfns.oonook.models.SetupRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SetupService {

    private final Firestore firestore;

    public Mono<Boolean> saveSetup(SetupRequest request) {
        return Mono.fromCallable(() -> {
            String userId = request.userId();

            // medication/data
            Map<String, Object> medicationData = new HashMap<>();
            medicationData.put("patient_name", request.patientName());
            medicationData.put("medications", request.medications());
            firestore.collection("agent_memory")
                    .document(userId)
                    .collection("medication")
                    .document("data")
                    .set(medicationData)
                    .get();

            // people/data
            Map<String, Object> peopleData = new HashMap<>();
            peopleData.put("contacts", request.contacts());
            firestore.collection("agent_memory")
                    .document(userId)
                    .collection("people")
                    .document("data")
                    .set(peopleData)
                    .get();

            // checkup/data
            Map<String, Object> checkupData = new HashMap<>();
            checkupData.put("patient_name", request.patientName());
            checkupData.put("appointments", request.appointments());
            firestore.collection("agent_memory")
                    .document(userId)
                    .collection("checkup")
                    .document("data")
                    .set(checkupData)
                    .get();

            return true;
        });
    }
}
