package com.dsarp.analyzer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import javax.tools.ToolProvider;

final class FixtureCompiler {
    private FixtureCompiler() { }

    static Path project(Path root, Map<String, String> sources) throws IOException {
        Path sourceRoot = root.resolve("fixture-module/src/main/java");
        Path classes = root.resolve("fixture-module/target/classes");
        Files.createDirectories(classes);
        List<String> arguments = new ArrayList<>(List.of("--release", "17", "-d", classes.toString()));
        for (Map.Entry<String, String> entry : sources.entrySet()) {
            Path source = sourceRoot.resolve(entry.getKey().replace('.', '/') + ".java");
            Files.createDirectories(source.getParent());
            Files.writeString(source, entry.getValue());
            arguments.add(source.toString());
        }
        int exit = ToolProvider.getSystemJavaCompiler().run(null, null, null, arguments.toArray(String[]::new));
        if (exit != 0) {
            throw new IllegalStateException("Fixture compilation failed with exit " + exit);
        }
        return root;
    }
}
