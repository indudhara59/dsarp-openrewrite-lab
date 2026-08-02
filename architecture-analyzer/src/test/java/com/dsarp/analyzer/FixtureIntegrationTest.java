package com.dsarp.analyzer;

import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.assertj.core.api.Assertions.assertThat;

class FixtureIntegrationTest {
    @TempDir Path temporary;

    @Test
    void analyzesSmallCompiledProjectEndToEnd() throws Exception {
        Path project = FixtureCompiler.project(temporary, Map.of(
                "com.dsarp.shop.alpha.Alpha", "package com.dsarp.shop.alpha; import com.dsarp.shop.beta.Beta; public class Alpha { public Beta create(){ return new Beta(); } }",
                "com.dsarp.shop.beta.Beta", "package com.dsarp.shop.beta; public class Beta {}"));
        AnalysisResult result = new ArchitectureAnalyzer().analyze(project, true);
        assertThat(result.classes()).hasSize(2);
        assertThat(result.classDependencies()).containsExactly(
                new DependencyEdge("com.dsarp.shop.alpha.Alpha", "com.dsarp.shop.beta.Beta"));
        assertThat(result.componentDependencies()).containsExactly(new ComponentEdge("alpha", "beta", 1));
        assertThat(result.unresolvedSymbolCount()).isZero();
    }
}
