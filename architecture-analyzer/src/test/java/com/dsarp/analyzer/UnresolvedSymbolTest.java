package com.dsarp.analyzer;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class UnresolvedSymbolTest {
    @TempDir Path temporary;

    @Test
    void recordsMissingInternalBytecodeAndStrictModeRejectsOverOnePercent() throws Exception {
        Path project = FixtureCompiler.project(temporary, Map.of(
                "com.dsarp.shop.alpha.Subject", "package com.dsarp.shop.alpha; import com.dsarp.shop.beta.Missing; public class Subject { Missing value; }",
                "com.dsarp.shop.beta.Missing", "package com.dsarp.shop.beta; public class Missing {}"));
        Files.delete(project.resolve("fixture-module/target/classes/com/dsarp/shop/beta/Missing.class"));
        AnalysisResult permissive = new ArchitectureAnalyzer().analyze(project, false);
        assertThat(permissive.unresolvedSymbolCount()).isPositive();
        assertThatThrownBy(() -> new ArchitectureAnalyzer().analyze(project, true))
                .isInstanceOf(IllegalStateException.class).hasMessageContaining("exceeds strict limit");
    }
}
