package com.dsarp.analyzer;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class GroundTruthIsolationTest {
    @Test
    void productionAnalyzerHasNoGroundTruthFileDependency() throws Exception {
        Path production = Path.of("src/main/java");
        try (var files = Files.walk(production)) {
            assertThat(files.filter(path -> path.toString().endsWith(".java"))
                    .map(path -> {
                        try {
                            return Files.readString(path);
                        } catch (Exception exception) {
                            throw new IllegalStateException(exception);
                        }
                    }))
                    .allMatch(text -> !text.contains("architecture-ground-truth.json"));
        }
    }
}
