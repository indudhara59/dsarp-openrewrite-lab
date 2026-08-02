# Verified OpenRewrite Sources

Recipe names and option names below were verified against official OpenRewrite documentation on 2026-08-02.

| Recipe | Verified options | Official source | Plan use |
|---|---|---|---|
| `org.openrewrite.java.ChangePackage` | `oldPackageName`, `newPackageName`, `recursive` | [Official catalog](https://docs.openrewrite.org/recipes/java/changepackage) | Seven scheduled package moves; investigated but unscheduled stable-contract move |
| `org.openrewrite.java.ChangeType` | `oldFullyQualifiedTypeName`, `newFullyQualifiedTypeName`, `ignoreDefinition` | [Official catalog](https://docs.openrewrite.org/recipes/java/changetype) | Not used: changing usages is not a substitute for moving declarations/source paths |
| `org.openrewrite.java.dependencies.ChangeDependency` | `oldGroupId`, `oldArtifactId`, `newGroupId`, `newArtifactId`, `newVersion`, `versionPattern`, `overrideManagedVersion`, `changeManagedDependency` | [Official catalog](https://docs.openrewrite.org/recipes/java/dependencies/changedependency) | Not used: no Maven coordinate changes are required |
| `org.openrewrite.java.dependencies.AddDependency` | `groupId`, `artifactId`, `version`, `versionPattern`, `onlyIfUsing`, `classifier`, `familyPattern`, `extension`, `configuration`, `scope`, `releasesOnly`, `type`, `optional`, `acceptTransitive` | [Official catalog](https://docs.openrewrite.org/recipes/java/dependencies/adddependency) | Not used: package moves remain within one Maven module |
| `org.openrewrite.java.dependencies.RemoveDependency` | `groupId`, `artifactId`, `unlessUsing`, `configuration`, `scope` | [Official catalog](https://docs.openrewrite.org/recipes/java/dependencies/removedependency) | Not used: no module dependency is removed |

The official [declarative recipe guide](https://docs.openrewrite.org/running-recipes/popular-recipe-guides/authoring-declarative-yaml-recipes) confirms that `ChangePackage` updates sources referencing the old package and moves package members to directories matching the new package. The official [getting-started guide](https://docs.openrewrite.org/running-recipes/getting-started) likewise demonstrates updated imports and moved source files.

No recipe or option lacking an official source is scheduled. No arbitrary class/method decomposition is represented as `ChangePackage`.
