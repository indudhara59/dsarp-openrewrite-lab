package com.dsarp.analyzer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Recursive validator for the JSON Schema subset used by the analyzer's versioned contracts. */
final class SchemaValidator {
    private static final List<String> REPORTS = List.of(
            "classes", "class_dependencies", "component_dependencies",
            "component_metrics", "responsibility_clusters", "analyzer_metadata");

    void validateAll(Path output, Path schemas) throws IOException {
        for (String name : REPORTS) {
            Path report = output.resolve(name + ".json");
            Path schemaFile = schemas.resolve(name + ".schema.json");
            if (!Files.isRegularFile(report) || !Files.isRegularFile(schemaFile)) {
                throw new IOException("Missing report or schema for " + name);
            }
            try {
                Object instance = JsonParser.parse(Files.readString(report));
                Object schema = JsonParser.parse(Files.readString(schemaFile));
                validate(instance, object(schema, "$"), "$", schemaFile);
            } catch (IllegalArgumentException exception) {
                throw new IOException("Schema validation failed for " + report + ": "
                        + exception.getMessage(), exception);
            }
        }
    }

    private void validate(Object value, Map<String, Object> schema, String path, Path schemaFile) {
        if (schema.containsKey("const") && !sameScalar(value, schema.get("const"))) {
            fail(path, "does not equal const " + schema.get("const"));
        }
        String type = (String) schema.get("type");
        if (type != null && !hasType(value, type)) fail(path, "must be " + type);
        if (value instanceof Map<?, ?> rawMap) validateObject(castMap(rawMap), schema, path, schemaFile);
        if (value instanceof List<?> list) validateArray(list, schema, path, schemaFile);
        if (value instanceof Number number) validateNumber(number, schema, path);
    }

    private void validateObject(Map<String, Object> value, Map<String, Object> schema,
            String path, Path schemaFile) {
        List<?> required = schema.get("required") instanceof List<?> list ? list : List.of();
        for (Object key : required) if (!value.containsKey(String.valueOf(key))) fail(path, "missing " + key);
        Map<String, Object> properties = schema.get("properties") instanceof Map<?, ?> map
                ? castMap(map) : Map.of();
        if (Boolean.FALSE.equals(schema.get("additionalProperties"))) {
            for (String key : value.keySet()) if (!properties.containsKey(key)) fail(path, "unexpected " + key);
        }
        for (Map.Entry<String, Object> entry : value.entrySet()) {
            if (properties.get(entry.getKey()) instanceof Map<?, ?> child) {
                validate(entry.getValue(), castMap(child), path + "." + entry.getKey(), schemaFile);
            }
        }
    }

    private void validateArray(List<?> value, Map<String, Object> schema, String path, Path schemaFile) {
        if (Boolean.TRUE.equals(schema.get("uniqueItems")) && new HashSet<>(value).size() != value.size()) {
            fail(path, "must contain unique items");
        }
        if (schema.get("items") instanceof Map<?, ?> child) {
            for (int index = 0; index < value.size(); index++) {
                validate(value.get(index), castMap(child), path + "[" + index + "]", schemaFile);
            }
        }
    }

    private void validateNumber(Number value, Map<String, Object> schema, String path) {
        if (schema.get("minimum") instanceof Number minimum && value.doubleValue() < minimum.doubleValue())
            fail(path, "is below minimum");
        if (schema.get("maximum") instanceof Number maximum && value.doubleValue() > maximum.doubleValue())
            fail(path, "is above maximum");
    }

    private boolean hasType(Object value, String type) {
        return switch (type) {
            case "object" -> value instanceof Map;
            case "array" -> value instanceof List;
            case "string" -> value instanceof String;
            case "integer" -> value instanceof Byte || value instanceof Short || value instanceof Integer
                    || value instanceof Long;
            case "number" -> value instanceof Number;
            case "boolean" -> value instanceof Boolean;
            case "null" -> value == null;
            default -> throw new IllegalArgumentException("Unsupported schema type " + type);
        };
    }

    private boolean sameScalar(Object left, Object right) {
        if (left instanceof Number a && right instanceof Number b) return a.doubleValue() == b.doubleValue();
        return java.util.Objects.equals(left, right);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> castMap(Map<?, ?> value) {
        return (Map<String, Object>) value;
    }

    private Map<String, Object> object(Object value, String path) {
        if (!(value instanceof Map<?, ?> map)) fail(path, "schema must be an object");
        return castMap((Map<?, ?>) value);
    }

    private void fail(String path, String message) {
        throw new IllegalArgumentException(path + " " + message);
    }
}
