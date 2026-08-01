# Glossary

## Architectural smell

A recurring structural condition that may indicate degraded modularity, maintainability, evolvability, or adherence to architecture principles. A smell is evidence for investigation, not proof of a defect.

## God Component

A component with disproportionate size, responsibilities, or dependency influence relative to peer components, suggesting insufficient separation of concerns.

## Stable Dependencies Principle

The principle that dependencies should point in the direction of stability: less stable components should depend on more stable components rather than the reverse.

## Afferent coupling

The number of external components that depend on a component, commonly denoted `Ca`. It represents incoming component dependencies.

## Efferent coupling

The number of external components on which a component depends, commonly denoted `Ce`. It represents outgoing component dependencies.

## Instability

A normalized measure of a component's susceptibility to change, commonly calculated as `I = Ce / (Ca + Ce)`. Values approach `0` for maximally stable components and `1` for maximally unstable components. The zero-coupling case must be handled explicitly by the analyzer.

## Refactoring candidate

A component, dependency, class, or related source element identified by analysis as potentially benefiting from a structural change.

## Refactoring recommendation

A ranked, evidence-backed proposal describing a candidate change, its rationale, intended architectural effect, constraints, and validation requirements.

## Declarative OpenRewrite recipe

An OpenRewrite recipe composed primarily through configuration from existing recipes, without custom visitor implementation.

## Imperative OpenRewrite recipe

An OpenRewrite recipe implemented with custom program logic and visitors to inspect or transform a Lossless Semantic Tree.

## Lossless Semantic Tree

OpenRewrite's source representation, which retains formatting and source details while adding semantic information needed for accurate analysis and transformation.

## Dry run

Execution that calculates and reports proposed transformations, usually as diffs, without applying those changes to the working source files.

## Type attribution

The association of syntax-tree elements with resolved type and symbol information, enabling transformations to distinguish elements by their semantic identity rather than text alone.

## Ground truth

The independently documented expected architecture smells and relevant source locations used to evaluate detector output after blind analysis.

## False positive

A reported smell or candidate that is not present according to the defined ground truth and evaluation rules.

## False negative

A ground-truth smell or candidate that the detector fails to report under the defined matching rules.
