package com.pmfns.oonook.models;

import lombok.Builder;

@Builder
public record ErrorResponse(String error, String message, String fallbackResponse) {
}
