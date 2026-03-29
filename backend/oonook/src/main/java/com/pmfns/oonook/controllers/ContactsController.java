package com.pmfns.oonook.controllers;

import com.pmfns.oonook.models.Contact;
import com.pmfns.oonook.repositories.ContactRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/contacts")
public class ContactsController {

    private final ContactRepository contactRepository;

    @GetMapping
    public Mono<ResponseEntity<Map<String, List<Contact>>>> getContacts(@RequestParam("user_id") String userId) {
        return contactRepository.findAllByUserId(userId)
                .collectList()
                .map(contacts -> ResponseEntity.ok(Map.of("contacts", contacts)));
    }

    @PostMapping("/{contactId}/image")
    public Mono<ResponseEntity<Map<String, Boolean>>> saveImage(
            @PathVariable String contactId,
            @RequestBody Map<String, String> body) {
        return contactRepository.findById(contactId)
                .flatMap(contact -> {
                    contact.setImageBase64(body.get("image_base64"));
                    return contactRepository.save(contact);
                })
                .map(c -> ResponseEntity.<Map<String, Boolean>>ok(Map.of("saved", true)))
                .defaultIfEmpty(ResponseEntity.notFound().<Map<String, Boolean>>build());
    }
}
