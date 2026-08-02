package com.dsarp.analyzer;

import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.assertj.core.api.Assertions.assertThat;

class ClassFileParserTest {
    @TempDir Path temporary;

    @Test
    void resolvesGenericArgumentsInheritanceAndInterfaces() throws Exception {
        Path project = FixtureCompiler.project(temporary, Map.of(
                "com.dsarp.shop.fixture.Parent", "package com.dsarp.shop.fixture; public class Parent {}",
                "com.dsarp.shop.fixture.Marker", "package com.dsarp.shop.fixture; public interface Marker {}",
                "com.dsarp.shop.fixture.Target", "package com.dsarp.shop.fixture; public class Target {}",
                "com.dsarp.shop.fixture.Subject", "package com.dsarp.shop.fixture; import java.util.List; public class Subject extends Parent implements Marker { private List<Target> values; public List<Target> values(){ return values; } }"));
        ParsedClass parsed = new ClassFileParser().parse(project.resolve(
                "fixture-module/target/classes/com/dsarp/shop/fixture/Subject.class"));
        assertThat(parsed.referencedClasses()).contains(
                "com.dsarp.shop.fixture.Parent",
                "com.dsarp.shop.fixture.Marker",
                "com.dsarp.shop.fixture.Target");
    }

    @Test
    void collapsesDuplicateSemanticReferencesToOneClassEdge() throws Exception {
        Path project = FixtureCompiler.project(temporary, Map.of(
                "com.dsarp.shop.fixture.Target", "package com.dsarp.shop.fixture; public class Target { public static int VALUE = 1; }",
                "com.dsarp.shop.fixture.Subject", "package com.dsarp.shop.fixture; public class Subject { Target field = new Target(); Target use(Target value) { return Target.VALUE > 0 ? value : new Target(); } }"));
        ParsedClass parsed = new ClassFileParser().parse(project.resolve(
                "fixture-module/target/classes/com/dsarp/shop/fixture/Subject.class"));
        assertThat(parsed.referencedClasses().stream()
                .filter(name -> name.equals("com.dsarp.shop.fixture.Target"))).hasSize(1);
    }
}
