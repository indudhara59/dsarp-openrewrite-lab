package com.dsarp.analyzer;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Strict JSON parser used only to validate generated reports and versioned schemas. */
final class JsonParser {
    private final String input;
    private int position;

    private JsonParser(String input) {
        this.input = input;
    }

    static Object parse(String input) {
        JsonParser parser = new JsonParser(input);
        Object value = parser.value();
        parser.whitespace();
        if (parser.position != input.length()) {
            throw parser.error("Trailing input");
        }
        return value;
    }

    private Object value() {
        whitespace();
        if (position >= input.length()) throw error("Expected value");
        return switch (input.charAt(position)) {
            case '{' -> object();
            case '[' -> array();
            case '"' -> string();
            case 't' -> literal("true", Boolean.TRUE);
            case 'f' -> literal("false", Boolean.FALSE);
            case 'n' -> literal("null", null);
            default -> number();
        };
    }

    private Map<String, Object> object() {
        expect('{');
        Map<String, Object> result = new LinkedHashMap<>();
        whitespace();
        if (take('}')) return result;
        do {
            whitespace();
            String key = string();
            whitespace();
            expect(':');
            result.put(key, value());
            whitespace();
        } while (take(','));
        expect('}');
        return result;
    }

    private List<Object> array() {
        expect('[');
        List<Object> result = new ArrayList<>();
        whitespace();
        if (take(']')) return result;
        do {
            result.add(value());
            whitespace();
        } while (take(','));
        expect(']');
        return result;
    }

    private String string() {
        expect('"');
        StringBuilder result = new StringBuilder();
        while (position < input.length()) {
            char character = input.charAt(position++);
            if (character == '"') return result.toString();
            if (character != '\\') {
                result.append(character);
                continue;
            }
            if (position >= input.length()) throw error("Incomplete escape");
            char escaped = input.charAt(position++);
            switch (escaped) {
                case '"', '\\', '/' -> result.append(escaped);
                case 'b' -> result.append('\b');
                case 'f' -> result.append('\f');
                case 'n' -> result.append('\n');
                case 'r' -> result.append('\r');
                case 't' -> result.append('\t');
                case 'u' -> {
                    if (position + 4 > input.length()) throw error("Incomplete unicode escape");
                    result.append((char) Integer.parseInt(input.substring(position, position + 4), 16));
                    position += 4;
                }
                default -> throw error("Invalid escape");
            }
        }
        throw error("Unterminated string");
    }

    private Number number() {
        int start = position;
        if (take('-')) { }
        while (position < input.length() && Character.isDigit(input.charAt(position))) position++;
        if (take('.')) while (position < input.length() && Character.isDigit(input.charAt(position))) position++;
        if (position < input.length() && (input.charAt(position) == 'e' || input.charAt(position) == 'E')) {
            position++;
            if (position < input.length() && (input.charAt(position) == '+' || input.charAt(position) == '-')) position++;
            while (position < input.length() && Character.isDigit(input.charAt(position))) position++;
        }
        if (start == position) throw error("Expected number");
        String text = input.substring(start, position);
        if (text.contains(".") || text.contains("e") || text.contains("E")) {
            return Double.parseDouble(text);
        }
        return Long.parseLong(text);
    }

    private Object literal(String text, Object value) {
        if (!input.startsWith(text, position)) throw error("Expected " + text);
        position += text.length();
        return value;
    }

    private void whitespace() {
        while (position < input.length() && Character.isWhitespace(input.charAt(position))) position++;
    }

    private boolean take(char expected) {
        if (position < input.length() && input.charAt(position) == expected) {
            position++;
            return true;
        }
        return false;
    }

    private void expect(char expected) {
        if (!take(expected)) throw error("Expected " + expected);
    }

    private IllegalArgumentException error(String message) {
        return new IllegalArgumentException(message + " at character " + position);
    }
}
