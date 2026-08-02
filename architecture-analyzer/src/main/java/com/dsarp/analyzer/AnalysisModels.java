package com.dsarp.analyzer;

import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;

record ParsedClass(String className, int access, int methodCount, Set<String> referencedClasses) { }

record SourceUnit(String className, Path file, String module, String packageName, int loc) { }

record ClassRecord(
        String className,
        String sourceFile,
        String module,
        String component,
        String packageName,
        int loc,
        List<String> outgoing,
        List<String> incoming,
        int publicTypeCount,
        int methodCount) { }

record DependencyEdge(String source, String target) { }

record ComponentEdge(String source, String target, int weight) { }

record ComponentMetric(
        String component,
        int productionClassCount,
        int productionLoc,
        int packageCount,
        int ca,
        int ce,
        double instability,
        List<String> incomingComponentEdges,
        List<String> outgoingComponentEdges,
        int weightedIncomingDependencyCount,
        int weightedOutgoingDependencyCount,
        int fanIn,
        int fanOut,
        int internalClassDependencyCount,
        double internalDependencyDensity,
        double percentageTotalClasses,
        double percentageTotalLoc,
        double degreeCentrality) { }

record ResponsibilityCluster(
        String clusterId,
        String component,
        List<String> memberClasses,
        List<String> dominantNameTokens,
        String dominantSubpackage,
        int internalEdgeCount,
        int outgoingEdgeCount,
        double cohesionScore,
        double confidence,
        List<String> evidence) { }

record AnalysisResult(
        List<ClassRecord> classes,
        List<DependencyEdge> classDependencies,
        List<ComponentEdge> componentDependencies,
        List<ComponentMetric> componentMetrics,
        List<ResponsibilityCluster> clusters,
        List<String> sourceRoots,
        List<String> excludedRoots,
        int unresolvedSymbolCount,
        int internalReferenceCount,
        List<String> warnings,
        Map<String, Object> metadata) { }
