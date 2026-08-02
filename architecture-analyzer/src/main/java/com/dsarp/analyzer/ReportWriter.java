package com.dsarp.analyzer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/** Writes stable JSON and RFC-4180-compatible CSV analysis artifacts. */
final class ReportWriter {
    static final String SCHEMA_VERSION = "1.0";

    void write(AnalysisResult result, Path output) throws IOException {
        Files.createDirectories(output);
        writeJson(output.resolve("classes.json"), "classes", result.classes().stream().map(this::classMap).toList());
        writeJson(output.resolve("class_dependencies.json"), "class_dependencies",
                result.classDependencies().stream().map(this::classEdgeMap).toList());
        writeJson(output.resolve("component_dependencies.json"), "component_dependencies",
                result.componentDependencies().stream().map(this::componentEdgeMap).toList());
        writeJson(output.resolve("component_metrics.json"), "component_metrics",
                result.componentMetrics().stream().map(this::metricMap).toList());
        writeJson(output.resolve("responsibility_clusters.json"), "responsibility_clusters",
                result.clusters().stream().map(this::clusterMap).toList());
        Files.writeString(output.resolve("analyzer_metadata.json"), Json.write(metadataMap(result)));

        writeCsv(output.resolve("classes.csv"),
                List.of("class_name", "source_file", "module", "component", "package", "loc",
                        "outgoing_dependency_count", "incoming_dependency_count", "public_type_count", "method_count"),
                result.classes(), record -> List.of(record.className(), record.sourceFile(), record.module(),
                        record.component(), record.packageName(), record.loc(), record.outgoing().size(),
                        record.incoming().size(), record.publicTypeCount(), record.methodCount()));
        writeCsv(output.resolve("class_dependencies.csv"), List.of("source", "target"),
                result.classDependencies(), edge -> List.of(edge.source(), edge.target()));
        writeCsv(output.resolve("component_dependencies.csv"), List.of("source", "target", "weight"),
                result.componentDependencies(), edge -> List.of(edge.source(), edge.target(), edge.weight()));
        writeCsv(output.resolve("component_metrics.csv"),
                List.of("component", "production_class_count", "production_loc", "package_count", "ca", "ce",
                        "instability", "weighted_incoming_dependency_count", "weighted_outgoing_dependency_count",
                        "fan_in", "fan_out", "internal_class_dependency_count", "internal_dependency_density",
                        "percentage_total_classes", "percentage_total_loc", "degree_centrality"),
                result.componentMetrics(), metric -> List.of(metric.component(), metric.productionClassCount(),
                        metric.productionLoc(), metric.packageCount(), metric.ca(), metric.ce(), metric.instability(),
                        metric.weightedIncomingDependencyCount(), metric.weightedOutgoingDependencyCount(),
                        metric.fanIn(), metric.fanOut(), metric.internalClassDependencyCount(),
                        metric.internalDependencyDensity(), metric.percentageTotalClasses(),
                        metric.percentageTotalLoc(), metric.degreeCentrality()));
        writeCsv(output.resolve("responsibility_clusters.csv"),
                List.of("cluster_id", "component", "member_count", "dominant_name_tokens", "dominant_subpackage",
                        "internal_edge_count", "outgoing_edge_count", "cohesion_score", "confidence"),
                result.clusters(), cluster -> List.of(cluster.clusterId(), cluster.component(),
                        cluster.memberClasses().size(), String.join("|", cluster.dominantNameTokens()),
                        cluster.dominantSubpackage(), cluster.internalEdgeCount(), cluster.outgoingEdgeCount(),
                        cluster.cohesionScore(), cluster.confidence()));
    }

    private void writeJson(Path file, String key, List<Map<String, Object>> rows) throws IOException {
        Map<String, Object> root = new LinkedHashMap<>();
        root.put("schema_version", SCHEMA_VERSION);
        root.put(key, rows);
        Files.writeString(file, Json.write(root));
    }

    private Map<String, Object> classMap(ClassRecord value) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("fully_qualified_class_name", value.className());
        map.put("source_file", value.sourceFile());
        map.put("maven_module", value.module());
        map.put("top_level_component", value.component());
        map.put("package", value.packageName());
        map.put("loc", value.loc());
        map.put("outgoing_class_dependencies", value.outgoing());
        map.put("incoming_class_dependencies", value.incoming());
        map.put("public_type_count", value.publicTypeCount());
        map.put("method_count", value.methodCount());
        return map;
    }

    private Map<String, Object> classEdgeMap(DependencyEdge value) {
        return linked("source_class", value.source(), "target_class", value.target());
    }

    private Map<String, Object> componentEdgeMap(ComponentEdge value) {
        return linked("source_component", value.source(), "target_component", value.target(), "weight", value.weight());
    }

    private Map<String, Object> metricMap(ComponentMetric value) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("component", value.component());
        map.put("production_class_count", value.productionClassCount());
        map.put("production_loc", value.productionLoc());
        map.put("package_count", value.packageCount());
        map.put("ca", value.ca());
        map.put("ce", value.ce());
        map.put("instability", value.instability());
        map.put("incoming_component_edges", value.incomingComponentEdges());
        map.put("outgoing_component_edges", value.outgoingComponentEdges());
        map.put("weighted_incoming_dependency_count", value.weightedIncomingDependencyCount());
        map.put("weighted_outgoing_dependency_count", value.weightedOutgoingDependencyCount());
        map.put("fan_in", value.fanIn());
        map.put("fan_out", value.fanOut());
        map.put("internal_class_dependency_count", value.internalClassDependencyCount());
        map.put("internal_dependency_density", value.internalDependencyDensity());
        map.put("percentage_total_production_classes", value.percentageTotalClasses());
        map.put("percentage_total_production_loc", value.percentageTotalLoc());
        map.put("degree_centrality", value.degreeCentrality());
        return map;
    }

    private Map<String, Object> clusterMap(ResponsibilityCluster value) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("cluster_id", value.clusterId());
        map.put("component", value.component());
        map.put("member_classes", value.memberClasses());
        map.put("dominant_name_tokens", value.dominantNameTokens());
        map.put("dominant_subpackage", value.dominantSubpackage());
        map.put("internal_edge_count", value.internalEdgeCount());
        map.put("outgoing_edge_count", value.outgoingEdgeCount());
        map.put("cohesion_score", value.cohesionScore());
        map.put("confidence", value.confidence());
        map.put("evidence", value.evidence());
        return map;
    }

    private Map<String, Object> metadataMap(AnalysisResult result) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("schema_version", SCHEMA_VERSION);
        map.putAll(result.metadata());
        map.put("included_source_roots", result.sourceRoots());
        map.put("excluded_source_roots", result.excludedRoots());
        map.put("formulas", Map.of(
                "instability", "Ce / (Ca + Ce), or 0 when Ca + Ce = 0",
                "internal_dependency_density", "directed internal class edges / (class_count * (class_count - 1))",
                "percentage_total_classes", "100 * component classes / total production classes",
                "percentage_total_loc", "100 * component LOC / total production LOC",
                "degree_centrality", "(Ca + Ce) / (component_count - 1)"));
        map.put("warnings", result.warnings());
        map.put("unresolved_symbol_count", result.unresolvedSymbolCount());
        map.put("internal_symbol_reference_count", result.internalReferenceCount());
        return map;
    }

    private Map<String, Object> linked(Object... values) {
        Map<String, Object> map = new LinkedHashMap<>();
        for (int index = 0; index < values.length; index += 2) {
            map.put(String.valueOf(values[index]), values[index + 1]);
        }
        return map;
    }

    private <T> void writeCsv(Path file, List<String> headers, List<T> rows,
            Function<T, List<Object>> mapper) throws IOException {
        List<String> lines = new ArrayList<>();
        lines.add(headers.stream().map(this::csv).collect(java.util.stream.Collectors.joining(",")));
        for (T row : rows) {
            lines.add(mapper.apply(row).stream().map(value -> csv(String.valueOf(value)))
                    .collect(java.util.stream.Collectors.joining(",")));
        }
        Files.write(file, lines);
    }

    private String csv(String value) {
        return "\"" + value.replace("\"", "\"\"") + "\"";
    }
}
