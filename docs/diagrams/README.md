# GR4ML Diagrams

The three GR4ML views are defined as editable PlantUML sources:

| View | Source | Rendered |
|------|--------|----------|
| Business View | `business_view.puml` | `business_view.png` / `.svg` |
| Analytics Design View | `analytics_design_view.puml` | `analytics_design_view.png` / `.svg` |
| Data Preparation View | `data_preparation_view.puml` | `data_preparation_view.png` / `.svg` |

## How to edit & re-render

Edit the `.puml` file, then re-render (Java required):

```bash
java -jar plantuml.jar -tpng -tsvg business_view.puml analytics_design_view.puml data_preparation_view.puml
```

`plantuml.jar` is included in this folder (v1.2024.7). Alternatives:

- **VS Code**: install the "PlantUML" extension → open a `.puml` → `Alt+D` to preview
- **Online**: paste the source into <https://www.plantuml.com/plantuml> or <https://plantuml-editor.kkeisuke.com>

## GR4ML notation mapping

| GR4ML element | PlantUML shape used |
|---------------|---------------------|
| Business / Decision (D) / Question (Q) goal | `usecase` (oval, D/Q prefix) |
| Analytics goal | `usecase` with thick border |
| Softgoal | `cloud` (✓ = satisfied) |
| Algorithm | `hexagon` |
| Insight (ML model card) / Entity | `rectangle` with attribute lines |
| Indicator | small `rectangle` with ██▲ mini-chart |
| Actor | `actor` (stick figure) |
| Operator | `rectangle` (pipeline step) |
| Parameters note | `note` (folded corner) |
| Data store | `database` (cylinder) |
| desires / generates / influence | dashed arrows; performs / evaluates / data flow: solid arrows |
