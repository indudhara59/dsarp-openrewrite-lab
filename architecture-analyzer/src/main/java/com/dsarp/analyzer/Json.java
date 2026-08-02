package com.dsarp.analyzer;

import java.util.Collection;
import java.util.Map;

/** Small deterministic JSON serializer for maps, collections and scalar report values. */
final class Json {
    private Json() { }

    static String write(Object value) {
        StringBuilder output = new StringBuilder();
        append(value, output, 0);
        output.append('\n');
        return output.toString();
    }

    private static void append(Object value, StringBuilder output, int depth) {
        if (value == null) {
            output.append("null");
        } else if (value instanceof String text) {
            quote(text, output);
        } else if (value instanceof Number || value instanceof Boolean) {
            output.append(value);
        } else if (value instanceof Map<?, ?> map) {
            output.append("{\n");
            int index = 0;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                indent(output, depth + 1);
                quote(String.valueOf(entry.getKey()), output);
                output.append(": ");
                append(entry.getValue(), output, depth + 1);
                if (++index < map.size()) {
                    output.append(',');
                }
                output.append('\n');
            }
            indent(output, depth);
            output.append('}');
        } else if (value instanceof Collection<?> collection) {
            output.append("[\n");
            int index = 0;
            for (Object item : collection) {
                indent(output, depth + 1);
                append(item, output, depth + 1);
                if (++index < collection.size()) {
                    output.append(',');
                }
                output.append('\n');
            }
            indent(output, depth);
            output.append(']');
        } else {
            throw new IllegalArgumentException("Unsupported JSON value " + value.getClass());
        }
    }

    private static void quote(String value, StringBuilder output) {
        output.append('"');
        for (int index = 0; index < value.length(); index++) {
            char character = value.charAt(index);
            switch (character) {
                case '"' -> output.append("\\\"");
                case '\\' -> output.append("\\\\");
                case '\b' -> output.append("\\b");
                case '\f' -> output.append("\\f");
                case '\n' -> output.append("\\n");
                case '\r' -> output.append("\\r");
                case '\t' -> output.append("\\t");
                default -> {
                    if (character < 0x20) {
                        output.append(String.format("\\u%04x", (int) character));
                    } else {
                        output.append(character);
                    }
                }
            }
        }
        output.append('"');
    }

    private static void indent(StringBuilder output, int depth) {
        output.append("  ".repeat(depth));
    }
}
