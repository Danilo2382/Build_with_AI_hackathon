package com.pmfns.oonook.models;

import com.google.cloud.firestore.annotation.DocumentId;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import com.google.cloud.spring.data.firestore.Document;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Document(collectionName = "reminders")
public class Reminder {

    @DocumentId
    private String id;
    private String userId;
    private String type;
    private String icon;
    private String label;
    private String time;
    private String status;
    private Integer daysSinceContact;
}
