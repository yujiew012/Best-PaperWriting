# Domain Template: Computer Systems & Distributed Computing

<!-- domain-id: distributed_systems. Standard template; sections 1-7 hold established conventions, section 8 holds provisional rules added by evolve-paper-skill. Rule ids (R-xxxx) refer to evolution_ledger.json. -->

> **Use when** the paper builds or optimizes a system: storage, scheduling, serving, distributed training, networking, OS/runtime. Read it together with `references/writing/*.md`.

## 1. Venues and reviewer expectations
- OSDI, SOSP, EuroSys, FAST, NSDI, TOCS and TPDS expect: a real implementation; realistic workloads; end-to-end gains explained by a measured bottleneck; artifact availability.
- Reviewers ask "where does the speedup come from?" and "does it hold at scale and under realistic load?"

## 2. Paper skeleton

| § | Section | Must contain |
| :--- | :--- | :--- |
| 1 | Introduction | Workload trend; a measured bottleneck in existing systems; insight; system name; headline results. |
| 2 | Background and motivation | Measurement study showing the bottleneck (with figures); why obvious fixes fail. |
| 3 | Design overview | Architecture figure; request or data path with numbered steps; key abstractions. |
| 4–5 | Design details | One section per mechanism: problem → design → why it is correct or efficient. |
| 6 | Implementation | Language, lines of code, integration points, what was modified. |
| 7 | Evaluation | Testbed; workloads and traces; baselines (production systems); end-to-end results; microbenchmarks; breakdown; scalability; sensitivity. |
| 8 | Discussion and related work | Generality; limitations; comparison by technique. |

## 3. Mandatory elements
- Testbed: CPU/GPU models, memory, network bandwidth, number of nodes, software versions.
- Workloads: real traces or standard benchmarks, with their parameters; why they are representative.
- Tail latency (P99/P99.9) alongside throughput; latency-throughput curves under increasing load.
- A performance breakdown that attributes the gain to each mechanism.

## 4. Evaluation protocol
- Compare against state-of-the-art and production-grade systems, configured as recommended by their authors.
- End-to-end first, then microbenchmarks and ablation (each mechanism on/off).
- Scalability: nodes, clients or data size, until the system saturates.
- Repeat runs; report variance or confidence intervals; warm-up and measurement duration.

## 5. Figures and tables
- Layered or pipeline architecture figure with numbered steps on the request path.
- Latency CDFs; throughput-latency curves; stacked time-breakdown bars; speedup vs. nodes.
- Motivation figures from the measurement study, in §2.

## 6. Narrative patterns
- "We observe X (measurement) → because Y (root cause) → so we design Z" for each mechanism.
- Attribute every speedup to a removed bottleneck (contention, copies, serialization, idle time) and show it in the breakdown.

## 7. Common rejection reasons → preventive checks
- Toy workloads → use production traces or standard benchmarks at realistic scale.
- Baselines misconfigured → document configuration and tuning.
- Average latency only → add tail latency and CDFs.
- No breakdown → add a per-mechanism ablation and time breakdown.

## 8. Provisional rules (evolution)

> Rules supported by a single exemplar paper. Treat them as suggestions. They become established (moved into §1–7) once a second paper supports them, and are retired if later papers contradict them.

_(none yet)_
