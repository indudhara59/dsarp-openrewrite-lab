package com.dsarp.analyzer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.stream.Collectors;

/** Coordinates semantic bytecode analysis and deterministic architecture aggregation. */
final class ArchitectureAnalyzer {
    static final String PACKAGE_PREFIX = "com.dsarp.shop.";
    static final String COMPONENT_RULE =
            "First package segment following com.dsarp.shop; subpackages remain in that component.";
    private static final int ACC_PUBLIC = 0x0001;
    private final ClassFileParser parser = new ClassFileParser();

    AnalysisResult analyze(Path project, boolean strict) throws IOException {
        Path root = project.toAbsolutePath().normalize();
        List<Path> sourceRoots = discoverSourceRoots(root);
        Map<String, SourceUnit> sources = discoverSources(root, sourceRoots);
        Map<String, ParsedClass> parsed = discoverClasses(root);
        Set<String> known = new TreeSet<>(parsed.keySet());
        known.retainAll(sources.keySet());

        int internalReferences = 0;
        int unresolved = 0;
        List<String> warnings = new ArrayList<>();
        Map<String, Set<String>> outgoing = new TreeMap<>();
        for (String className : known) {
            Set<String> resolved = new TreeSet<>();
            for (String reference : parsed.get(className).referencedClasses()) {
                if (!reference.startsWith(PACKAGE_PREFIX)) {
                    continue;
                }
                internalReferences++;
                String topLevel = topLevelName(reference);
                if (known.contains(topLevel) && !className.equals(topLevel)) {
                    resolved.add(topLevel);
                } else if (!className.equals(topLevel)) {
                    unresolved++;
                    warnings.add("Unresolved internal symbol: " + className + " -> " + reference);
                }
            }
            outgoing.put(className, resolved);
        }
        warnings = warnings.stream().distinct().sorted().toList();
        double unresolvedPercentage = internalReferences == 0 ? 0.0
                : (100.0 * unresolved / internalReferences);
        if (strict && unresolvedPercentage > 1.0) {
            throw new IllegalStateException("Unresolved internal symbol percentage "
                    + round(unresolvedPercentage) + "% exceeds strict limit 1.0%");
        }

        Map<String, Set<String>> incoming = invert(known, outgoing);
        List<ClassRecord> classes = createClassRecords(known, sources, parsed, outgoing, incoming);
        List<DependencyEdge> classEdges = createClassEdges(outgoing);
        List<ComponentEdge> componentEdges = createComponentEdges(classEdges);
        List<ComponentMetric> metrics = calculateMetrics(classes, classEdges, componentEdges);
        List<ResponsibilityCluster> clusters = cluster(classes, classEdges);

        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("analyzer_version", "1.0.0");
        metadata.put("execution_timestamp", Instant.now().toString());
        metadata.put("git_commit_sha", gitCommit(root));
        metadata.put("java_version", System.getProperty("java.version"));
        metadata.put("maven_version", "Apache Maven 3.9.9 (pinned wrapper distribution)");
        metadata.put("component_rule", COMPONENT_RULE);
        metadata.put("dependency_extraction_method",
                "JVM class-file semantic references: constant-pool class/member owners, descriptors, generic signatures, inheritance, interfaces, annotations and exception metadata");
        metadata.put("strict_mode", strict);
        metadata.put("unresolved_symbol_percentage", round(unresolvedPercentage));

        return new AnalysisResult(
                classes,
                classEdges,
                componentEdges,
                metrics,
                clusters,
                sourceRoots.stream().map(Path::toString).sorted().toList(),
                List.of("**/src/test/**", "**/target/generated-sources/**",
                        "architecture-analyzer/**", "dashboard/**", "Maven/plugin implementation classes"),
                unresolved,
                internalReferences,
                warnings,
                metadata);
    }

    private String gitCommit(Path project) {
        Path workingDirectory = Files.isDirectory(project.resolve(".git")) ? project : project.getParent();
        try {
            Process process = new ProcessBuilder("git", "rev-parse", "HEAD")
                    .directory(workingDirectory.toFile()).redirectErrorStream(true).start();
            String output = new String(process.getInputStream().readAllBytes()).strip();
            return process.waitFor() == 0 && !output.isBlank() ? output : "unavailable";
        } catch (IOException exception) {
            return "unavailable";
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            return "unavailable";
        }
    }

    static String componentOf(String packageName) {
        if (packageName == null || !packageName.startsWith(PACKAGE_PREFIX)) {
            throw new IllegalArgumentException("Package is outside " + PACKAGE_PREFIX + ": " + packageName);
        }
        String remainder = packageName.substring(PACKAGE_PREFIX.length());
        int separator = remainder.indexOf('.');
        return separator < 0 ? remainder : remainder.substring(0, separator);
    }

    private List<Path> discoverSourceRoots(Path project) throws IOException {
        try (var paths = Files.walk(project, 4)) {
            return paths.filter(Files::isDirectory)
                    .filter(path -> path.endsWith(Path.of("src", "main", "java")))
                    .filter(path -> !excluded(project, path))
                    .sorted()
                    .toList();
        }
    }

    private Map<String, SourceUnit> discoverSources(Path project, List<Path> roots) throws IOException {
        Map<String, SourceUnit> result = new TreeMap<>();
        for (Path sourceRoot : roots) {
            String module = sourceRoot.getParent().getParent().getParent().getFileName().toString();
            try (var paths = Files.walk(sourceRoot)) {
                for (Path file : paths.filter(path -> Files.isRegularFile(path)
                                && path.toString().endsWith(".java"))
                        .sorted().toList()) {
                    List<String> lines = Files.readAllLines(file);
                    String packageName = packageDeclaration(lines);
                    if (!packageName.startsWith(PACKAGE_PREFIX)) {
                        continue;
                    }
                    String simpleName = file.getFileName().toString();
                    simpleName = simpleName.substring(0, simpleName.length() - ".java".length());
                    String className = packageName + "." + simpleName;
                    result.put(className, new SourceUnit(className,
                            project.relativize(file.toAbsolutePath().normalize()), module,
                            packageName, lines.size()));
                }
            }
        }
        return result;
    }

    private Map<String, ParsedClass> discoverClasses(Path project) throws IOException {
        Map<String, ParsedClass> result = new TreeMap<>();
        try (var paths = Files.walk(project, 5)) {
            List<Path> classRoots = paths.filter(Files::isDirectory)
                    .filter(path -> path.endsWith(Path.of("target", "classes")))
                    .filter(path -> !excluded(project, path))
                    .sorted().toList();
            for (Path classRoot : classRoots) {
                try (var classPaths = Files.walk(classRoot)) {
                    for (Path classFile : classPaths.filter(path -> Files.isRegularFile(path)
                                    && path.toString().endsWith(".class"))
                            .sorted().toList()) {
                        ParsedClass parsedClass = parser.parse(classFile);
                        if (parsedClass.className().startsWith(PACKAGE_PREFIX)
                                && !parsedClass.className().contains("$")) {
                            result.put(parsedClass.className(), parsedClass);
                        }
                    }
                }
            }
        }
        return result;
    }

    private boolean excluded(Path project, Path path) {
        String normalized = path.toString().replace('\\', '/');
        Path relative = project.toAbsolutePath().normalize().relativize(path.toAbsolutePath().normalize());
        for (Path segment : relative) {
            String name = segment.toString();
            if ("architecture-analyzer".equals(name) || "dashboard".equals(name)) {
                return true;
            }
        }
        return normalized.contains("/src/test/") || normalized.contains("/generated-sources/");
    }

    private String packageDeclaration(List<String> lines) {
        for (String line : lines) {
            String value = line.strip();
            if (value.startsWith("package ")) {
                int terminator = value.indexOf(';');
                if (terminator > "package ".length()) {
                    return value.substring("package ".length(), terminator).strip();
                }
            }
        }
        return "";
    }

    private String topLevelName(String reference) {
        int nested = reference.indexOf('$');
        return nested < 0 ? reference : reference.substring(0, nested);
    }

    private Map<String, Set<String>> invert(Set<String> classes, Map<String, Set<String>> outgoing) {
        Map<String, Set<String>> incoming = new TreeMap<>();
        classes.forEach(name -> incoming.put(name, new TreeSet<>()));
        outgoing.forEach((source, targets) -> targets.forEach(target -> incoming.get(target).add(source)));
        return incoming;
    }

    private List<ClassRecord> createClassRecords(
            Set<String> names,
            Map<String, SourceUnit> sources,
            Map<String, ParsedClass> parsed,
            Map<String, Set<String>> outgoing,
            Map<String, Set<String>> incoming) {
        List<ClassRecord> records = new ArrayList<>();
        for (String name : names) {
            SourceUnit source = sources.get(name);
            ParsedClass bytecode = parsed.get(name);
            records.add(new ClassRecord(name, source.file().toString(), source.module(),
                    componentOf(source.packageName()), source.packageName(), source.loc(),
                    List.copyOf(outgoing.get(name)), List.copyOf(incoming.get(name)),
                    (bytecode.access() & ACC_PUBLIC) == 0 ? 0 : 1, bytecode.methodCount()));
        }
        return List.copyOf(records);
    }

    private List<DependencyEdge> createClassEdges(Map<String, Set<String>> outgoing) {
        List<DependencyEdge> edges = new ArrayList<>();
        outgoing.forEach((source, targets) -> targets.forEach(target -> edges.add(new DependencyEdge(source, target))));
        edges.sort(Comparator.comparing(DependencyEdge::source).thenComparing(DependencyEdge::target));
        return List.copyOf(edges);
    }

    private List<ComponentEdge> createComponentEdges(List<DependencyEdge> classEdges) {
        Map<String, Integer> weights = new TreeMap<>();
        for (DependencyEdge edge : classEdges) {
            String source = componentFromClass(edge.source());
            String target = componentFromClass(edge.target());
            if (!source.equals(target)) {
                weights.merge(source + "\u0000" + target, 1, Integer::sum);
            }
        }
        return weights.entrySet().stream().map(entry -> {
            String[] parts = entry.getKey().split("\u0000", -1);
            return new ComponentEdge(parts[0], parts[1], entry.getValue());
        }).toList();
    }

    static List<ComponentMetric> calculateMetrics(
            List<ClassRecord> classes,
            List<DependencyEdge> classEdges,
            List<ComponentEdge> componentEdges) {
        Map<String, List<ClassRecord>> grouped = classes.stream()
                .collect(Collectors.groupingBy(ClassRecord::component, TreeMap::new, Collectors.toList()));
        int totalClasses = classes.size();
        int totalLoc = classes.stream().mapToInt(ClassRecord::loc).sum();
        int componentCount = grouped.size();
        List<ComponentMetric> metrics = new ArrayList<>();
        for (Map.Entry<String, List<ClassRecord>> entry : grouped.entrySet()) {
            String component = entry.getKey();
            List<ClassRecord> members = entry.getValue();
            Set<String> incomingComponents = componentEdges.stream()
                    .filter(edge -> edge.target().equals(component)).map(ComponentEdge::source)
                    .collect(Collectors.toCollection(TreeSet::new));
            Set<String> outgoingComponents = componentEdges.stream()
                    .filter(edge -> edge.source().equals(component)).map(ComponentEdge::target)
                    .collect(Collectors.toCollection(TreeSet::new));
            int ca = incomingComponents.size();
            int ce = outgoingComponents.size();
            int weightedIn = componentEdges.stream().filter(edge -> edge.target().equals(component))
                    .mapToInt(ComponentEdge::weight).sum();
            int weightedOut = componentEdges.stream().filter(edge -> edge.source().equals(component))
                    .mapToInt(ComponentEdge::weight).sum();
            int internal = (int) classEdges.stream().filter(edge ->
                    componentFromClass(edge.source()).equals(component)
                            && componentFromClass(edge.target()).equals(component)).count();
            int size = members.size();
            double possible = size <= 1 ? 0.0 : (double) size * (size - 1);
            int loc = members.stream().mapToInt(ClassRecord::loc).sum();
            metrics.add(new ComponentMetric(component, size, loc,
                    (int) members.stream().map(ClassRecord::packageName).distinct().count(),
                    ca, ce, instability(ca, ce), List.copyOf(incomingComponents),
                    List.copyOf(outgoingComponents), weightedIn, weightedOut,
                    weightedIn, weightedOut, internal, possible == 0.0 ? 0.0 : round(internal / possible),
                    percentage(size, totalClasses), percentage(loc, totalLoc),
                    componentCount <= 1 ? 0.0 : round((double) (ca + ce) / (componentCount - 1))));
        }
        return List.copyOf(metrics);
    }

    static double instability(int ca, int ce) {
        return ca + ce == 0 ? 0.0 : round((double) ce / (ca + ce));
    }

    private List<ResponsibilityCluster> cluster(List<ClassRecord> classes, List<DependencyEdge> edges) {
        Map<String, List<ClassRecord>> groups = new TreeMap<>();
        for (ClassRecord record : classes) {
            String relative = record.packageName().substring((PACKAGE_PREFIX + record.component()).length());
            String subpackage = relative.startsWith(".") ? relative.substring(1) : relative;
            if (subpackage.contains(".")) {
                subpackage = subpackage.substring(0, subpackage.indexOf('.'));
            }
            if (subpackage.isBlank()) {
                subpackage = "root";
            }
            groups.computeIfAbsent(record.component() + ":" + subpackage, ignored -> new ArrayList<>())
                    .add(record);
        }
        List<ResponsibilityCluster> clusters = new ArrayList<>();
        for (Map.Entry<String, List<ClassRecord>> entry : groups.entrySet()) {
            List<String> members = entry.getValue().stream().map(ClassRecord::className).sorted().toList();
            Set<String> memberSet = Set.copyOf(members);
            int internalEdges = (int) edges.stream().filter(edge -> memberSet.contains(edge.source())
                    && memberSet.contains(edge.target())).count();
            int outgoingEdges = (int) edges.stream().filter(edge -> memberSet.contains(edge.source())
                    && !memberSet.contains(edge.target())).count();
            double possible = members.size() <= 1 ? 0.0 : (double) members.size() * (members.size() - 1);
            double cohesion = possible == 0.0 ? 1.0 : round(internalEdges / possible);
            Map<String, Integer> tokens = new TreeMap<>();
            for (String member : members) {
                String simple = member.substring(member.lastIndexOf('.') + 1);
                for (String token : nameTokens(simple)) {
                    if (token.length() > 2 && !Set.of("service", "adapter", "policy").contains(token)) {
                        tokens.merge(token, 1, Integer::sum);
                    }
                }
            }
            List<String> dominantTokens = tokens.entrySet().stream()
                    .sorted(Map.Entry.<String, Integer>comparingByValue().reversed()
                            .thenComparing(Map.Entry::getKey))
                    .limit(5).map(Map.Entry::getKey).toList();
            String subpackage = entry.getKey().substring(entry.getKey().indexOf(':') + 1);
            String component = entry.getValue().get(0).component();
            double connectivity = Math.min(1.0, cohesion * 4.0);
            double tokenSignal = dominantTokens.isEmpty() ? 0.0 : 1.0;
            double profileSimilarity = dependencyProfileSimilarity(members, edges);
            double confidence = round(0.4 + 0.25 * connectivity + 0.15 * tokenSignal
                    + 0.2 * profileSimilarity);
            clusters.add(new ResponsibilityCluster(
                    "cluster:" + entry.getKey(), component, members, dominantTokens, subpackage,
                    internalEdges, outgoingEdges, cohesion, confidence,
                    List.of("shared top-level subpackage=" + subpackage,
                            "internal connectivity edges=" + internalEdges,
                            "common class-name tokens=" + String.join(",", dominantTokens),
                            "common dependency profile similarity=" + profileSimilarity,
                            "outgoing edges=" + outgoingEdges)));
        }
        return List.copyOf(clusters);
    }

    private double dependencyProfileSimilarity(List<String> members, List<DependencyEdge> edges) {
        if (members.size() <= 1) {
            return 1.0;
        }
        Map<String, Set<String>> profiles = new TreeMap<>();
        for (String member : members) {
            Set<String> targets = edges.stream().filter(edge -> edge.source().equals(member))
                    .map(edge -> componentFromClass(edge.target()))
                    .collect(Collectors.toCollection(TreeSet::new));
            profiles.put(member, targets);
        }
        double total = 0.0;
        int pairs = 0;
        for (int left = 0; left < members.size(); left++) {
            for (int right = left + 1; right < members.size(); right++) {
                Set<String> union = new TreeSet<>(profiles.get(members.get(left)));
                union.addAll(profiles.get(members.get(right)));
                Set<String> intersection = new TreeSet<>(profiles.get(members.get(left)));
                intersection.retainAll(profiles.get(members.get(right)));
                total += union.isEmpty() ? 1.0 : (double) intersection.size() / union.size();
                pairs++;
            }
        }
        return round(total / pairs);
    }

    static List<String> nameTokens(String name) {
        List<String> tokens = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        for (int index = 0; index < name.length(); index++) {
            char character = name.charAt(index);
            if (Character.isUpperCase(character) && !current.isEmpty()) {
                tokens.add(current.toString().toLowerCase(Locale.ROOT));
                current.setLength(0);
            }
            if (Character.isLetterOrDigit(character)) {
                current.append(character);
            }
        }
        if (!current.isEmpty()) {
            tokens.add(current.toString().toLowerCase(Locale.ROOT));
        }
        return List.copyOf(tokens);
    }

    private static String componentFromClass(String className) {
        int packageEnd = className.lastIndexOf('.');
        return componentOf(className.substring(0, packageEnd));
    }

    private static double percentage(int part, int total) {
        return total == 0 ? 0.0 : round(100.0 * part / total);
    }

    static double round(double value) {
        return Math.round(value * 1_000_000.0) / 1_000_000.0;
    }
}
