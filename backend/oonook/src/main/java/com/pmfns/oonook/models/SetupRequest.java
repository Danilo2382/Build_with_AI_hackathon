package com.pmfns.oonook.models;

import java.util.List;

public record SetupRequest(
        String userId,
        String patientName,
        List<Medication> medications,
        List<Contact> contacts,
        List<Appointment> appointments
) {
    public record Medication(String name, String dose, String time) {}
    public record Contact(String name, String relationship) {}
    public record Appointment(String doctor, String date) {}
}
