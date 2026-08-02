package com.dsarp.analyzer;

import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;

/** Command-line entry point for analysis and schema validation. */
public final class AnalyzerCli {
    private AnalyzerCli() { }

    public static void main(String[] args) {
        try {
            int exit = execute(args);
            if (exit != 0) {
                System.exit(exit);
            }
        } catch (Exception exception) {
            System.err.println("Analyzer failed: " + exception.getMessage());
            System.exit(2);
        }
    }

    static int execute(String[] args) throws Exception {
        if (args.length == 0 || "--help".equals(args[0])) {
            usage();
            return args.length == 0 ? 1 : 0;
        }
        String command = args[0];
        Map<String, String> options = options(Arrays.copyOfRange(args, 1, args.length));
        if ("analyze".equals(command)) {
            Path project = requiredPath(options, "--project");
            Path output = requiredPath(options, "--output");
            boolean strict = options.containsKey("--strict");
            AnalysisResult result = new ArchitectureAnalyzer().analyze(project, strict);
            new ReportWriter().write(result, output);
            System.out.printf("Analyzed %d classes and %d resolved class dependencies.%n",
                    result.classes().size(), result.classDependencies().size());
            System.out.printf("Unresolved symbols: %d of %d internal references.%n",
                    result.unresolvedSymbolCount(), result.internalReferenceCount());
            return 0;
        }
        if ("validate".equals(command)) {
            Path output = requiredPath(options, "--output");
            Path schemas = requiredPath(options, "--schemas");
            new SchemaValidator().validateAll(output, schemas);
            System.out.println("Validated 6 JSON reports against versioned schema contracts.");
            return 0;
        }
        usage();
        return 1;
    }

    private static Map<String, String> options(String[] args) {
        Map<String, String> result = new LinkedHashMap<>();
        for (int index = 0; index < args.length; index++) {
            String argument = args[index];
            if ("--strict".equals(argument)) {
                result.put(argument, "true");
            } else if (argument.startsWith("--") && index + 1 < args.length) {
                result.put(argument, args[++index]);
            } else {
                throw new IllegalArgumentException("Unexpected argument " + argument);
            }
        }
        return result;
    }

    private static Path requiredPath(Map<String, String> options, String name) {
        String value = options.get(name);
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Missing required option " + name);
        }
        return Path.of(value);
    }

    private static void usage() {
        System.out.println("Usage:");
        System.out.println("  analyze --project <path> --output <path> [--strict]");
        System.out.println("  validate --output <path> --schemas <path>");
    }
}
