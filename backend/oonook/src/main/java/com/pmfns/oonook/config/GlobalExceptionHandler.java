package com.pmfns.oonook.config;

import com.pmfns.oonook.models.ErrorResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.client.ResourceAccessException;

@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceAccessException.class)
    public ResponseEntity<ErrorResponse> handleAgentsUnavailable(ResourceAccessException ex) {
        ErrorResponse error = ErrorResponse.builder()
                .error("agents_unavailable")
                .message("Could not reach AI service: " + ex.getMessage())
                .fallbackResponse("Sorry, I am having trouble. Please try again.")
                .build();
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(error);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneralException(Exception ex) {
        ErrorResponse error = ErrorResponse.builder()
                .error("internal_error")
                .message("An unexpected error occurred: " + ex.getMessage())
                .fallbackResponse("Sorry, I am having trouble. Please try again.")
                .build();
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
