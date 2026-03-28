package com.pmfns.oonook.models;

public record ChatResponse(String response, String agent, Media media) {

    public record Media(String type, String url) {
    }
}
