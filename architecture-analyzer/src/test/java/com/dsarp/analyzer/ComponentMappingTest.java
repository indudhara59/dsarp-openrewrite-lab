package com.dsarp.analyzer;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ComponentMappingTest {
    @Test
    void mapsNestedPackagesToFirstSegmentAfterShop() {
        assertThat(ArchitectureAnalyzer.componentOf("com.dsarp.shop.megacomponent.payment"))
                .isEqualTo("megacomponent");
        assertThat(ArchitectureAnalyzer.componentOf("com.dsarp.shop.ordercore"))
                .isEqualTo("ordercore");
    }

    @Test
    void rejectsPackagesOutsideAnalysisBoundary() {
        assertThatThrownBy(() -> ArchitectureAnalyzer.componentOf("org.example.shop"))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
