# Figure Rubric (1–5 per dimension)

Score the generated diagram as a figure for the target venue, using the original as the reference for what "publishable" looks like. Judge communication, not likeness. Half points are allowed; the overall score is the mean (computed by `evolve.py score`).

| Dimension | 1 | 3 | 5 |
| :--- | :--- | :--- | :--- |
| `completeness` | Key entities or flows from the brief are missing | All entities present; some relations or groups missing | Every entity, relation, group and emphasis point of the brief is shown |
| `structure_clarity` | The topology (who talks to whom) is hard to see | Readable after study | The topology is obvious at a glance; groups match the roles they represent |
| `flow_readability` | Arrow directions or order are ambiguous | Order can be followed with effort | Numbered steps run in a natural reading order; no crossing or doubling back without reason |
| `emphasis` | The contribution does not stand out; adverse elements look like benign ones | Partly distinguished | The paper's contribution is the visual focus; adverse parties and trust boundaries are unmistakable |
| `domain_conventions` | Ignores the area's diagram conventions (e.g. no trust boundary in a security figure) | Most conventions present | Looks like a strong figure of this research area |
| `visual_quality` | Clutter, collisions, inconsistent sizes, unreadable text | Clean but uneven spacing or weight | Aligned, balanced, consistent, readable at print size |

## Calibration
- Different from the original is not worse. Only score down what makes the figure communicate less well.
- `completeness` is anchored to the brief: content the original shows but the brief omits is a `brief_missing` gap, not a completeness penalty.
- Score each figure on its own; do not adjust scores to show progress across iterations.
