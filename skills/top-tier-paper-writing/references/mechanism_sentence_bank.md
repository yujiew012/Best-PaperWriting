# Mechanism Mapping Sentence Bank (顶会顶刊机制归因经典句式库)

> 本句式库提炼自 CCF-A 顶会与顶级 IEEE/ACM Transactions 论文，专用于破解“实验只会报菜名堆数据”的通病，帮助作者将实证数据归因到自研方法的特定算法机制上。
>
> **使用前提**：下列句式默认已有消融或受控实验支持；只有相关证据时把 *attributed to / stems from* 换成 *is consistent with / suggests*，没有证据时写成假设（见 `writing/evaluation.md` 的归因证据阶梯）。

---

## 1. 核心组件直接归因句式（Component Direct Attribution）

- **归因于组件的能力**：
  > *"The superior performance of [Method] can be primarily attributed to [Component A]'s ability to [action], which effectively mitigates [challenge]."*
  - *范例*：*"The superior performance of FedPE can be primarily attributed to DDAP's ability to generate distribution-aligned prompts, which effectively mitigates feature misalignment under dynamic drift."*

- **分析表明组件发挥了作用**：
  > *"Analysis suggests that [Component A] is capable of [action], providing [benefit] that substantially enhances the adaptability to [scenario]."*
  - *范例*：*"Analysis suggests that DDAP is capable of rapid convergence with single-epoch meta-updates, providing accurate directional guidance that substantially enhances adaptability to unobserved client distributions."*

- **归因于对特定缺陷的抑制**：
  > *"This robustness is attributable to [Component B]'s effectiveness in suppressing [undesirable phenomenon]."*
  - *范例*：*"This sustained accuracy is attributable to PKM's effectiveness in suppressing catastrophic feature overwriting across successive communication rounds."*

---

## 2. 多组件协同效应归因句式（Synergistic Interaction Attribution）

- **双模块互补与相互赋能**：
  > *"The clear advantage in [metric] stems from the synergistic interactions between [Component A] and [Component B]: the former enables [action 1], while the latter enforces [action 2]."*
  - *范例*：*"The clear advantage in convergence stability stems from the synergistic interactions between DDAP and PKM: the former enables rapid distribution adaptation, while the latter enforces parameter continuity."*

- **联合维持潜在表征空间**：
  > *"The well-separated semantic clusters in Fig. 5 highlight the combined effect of [action 1] guided by [Component A] and [action 2] preserved by [Component B]. Together, these components maintain a coherent representation space despite severe data fluctuations."*

---

## 3. 架构解耦与不变性归因句式（Decoupling & Invariance Attribution）

- **跨主干网络解耦性论证**：
  > *"The negligible performance variance across distinct backbone architectures underscores the capability of [Method] to decouple [process 1] from [process 2]."*
  - *范例*：*"The negligible performance variance across distinct backbone architectures underscores the capability of FedPE to decouple distribution adaptation from backbone-specific feature learning."*

- **结构无关性与通用性对比**：
  > *"Unlike existing baselines whose performance is heavily contingent upon specific structural priors or inductive biases, [Method] is inherently architecture-agnostic."*

---

## 4. 行为轨迹差异与反事实对比句式（Counterfactual & Behavioral Comparison）

- **平滑轨迹 vs 震荡滑坡**：
  > *"While baselines exhibit a pronounced tendency towards catastrophic forgetting during distribution shifts (accompanied by severe accuracy fluctuations), [Method] maintains a coherent learning trajectory, capable of rapidly recovering from transient perturbations."*

- **揭示基线失效的深层机理**：
  > *"This disparity indicates that simply applying [baseline approach] fails to handle [challenge] because it lacks [mechanism], whereas our [Component] successfully establishes a robust decision boundary by [action]."*

---

## 5. 参数敏感性倒 U 型拐点权衡句式（Trade-off & Turning-Point Analysis）

- **权衡演化过程剖析**：
  > *"Our analysis reveals that as [parameter] increases, overall performance initially improves but subsequently declines. This behavior can be attributed to the progressive enhancement of [desirable capability] in the early stage. However, as [parameter] grows excessively, the model experiences [adverse effect], beginning to memorize noise in the training data rather than learning underlying generalizable patterns."*


### [Autonomous Evolution: 2026-11-23 02:25:49 from MinerU Exemplar: FedPE (Computer Networks 2025)]
#### Discovered Causal Attributions:
- `Both experimental configurations indicate that FedPE exhibits enhanced generalization capabilities as the client scale expands, attributable to PKM mechanism's effectiveness in suppressing feature overwriting.`


### [Autonomous Evolution: 2026-11-23 02:26:47 from arXiv Query: 'adversarial differential privacy' (3 papers)]
#### Discovered Causal Attributions:
- `S2L decouples speech content from hardware acoustics using a physics-constrained forward simulator.`
