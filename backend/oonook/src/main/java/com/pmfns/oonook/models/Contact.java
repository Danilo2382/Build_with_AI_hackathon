package com.pmfns.oonook.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.firestore.annotation.PropertyName;
import com.google.cloud.spring.data.firestore.Document;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Document(collectionName = "contacts")
public class Contact {

    @DocumentId
    private String id;

    private String userId;
    private String name;
    private String relationship;

    @PropertyName("emergency_contact")
    @JsonProperty("emergency_contact")
    private Boolean emergencyContact;

    @PropertyName("image_base64")
    @JsonProperty("image_base64")
    private String imageBase64;
}
