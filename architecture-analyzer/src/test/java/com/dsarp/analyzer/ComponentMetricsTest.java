package com.dsarp.analyzer;

import java.util.List;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class ComponentMetricsTest {
    @Test
    void calculatesDistinctCaCeAndInstability() {
        List<ClassRecord> classes = List.of(
                type("com.dsarp.shop.alpha.A", "alpha"),
                type("com.dsarp.shop.beta.B", "beta"),
                type("com.dsarp.shop.gamma.C", "gamma"));
        List<DependencyEdge> classEdges = List.of(
                new DependencyEdge(classes.get(0).className(), classes.get(1).className()),
                new DependencyEdge(classes.get(2).className(), classes.get(1).className()));
        List<ComponentEdge> componentEdges = List.of(
                new ComponentEdge("alpha", "beta", 1), new ComponentEdge("gamma", "beta", 1));

        ComponentMetric beta = ArchitectureAnalyzer.calculateMetrics(classes, classEdges, componentEdges)
                .stream().filter(metric -> metric.component().equals("beta")).findFirst().orElseThrow();
        assertThat(beta.ca()).isEqualTo(2);
        assertThat(beta.ce()).isZero();
        assertThat(beta.instability()).isZero();
        assertThat(ArchitectureAnalyzer.instability(1, 3)).isEqualTo(0.75);
        assertThat(ArchitectureAnalyzer.instability(0, 0)).isZero();
    }

    private ClassRecord type(String name, String component) {
        return new ClassRecord(name, name + ".java", "fixture", component,
                name.substring(0, name.lastIndexOf('.')), 10, List.of(), List.of(), 1, 1);
    }
}
