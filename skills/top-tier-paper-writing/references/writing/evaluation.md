# Evaluation（实验与评估）

> 适用：实验设置、结果分析段落、消融/敏感性/鲁棒性分析。归因句式见 [`../mechanism_sentence_bank.md`](../mechanism_sentence_bank.md)。

## 2.6 Evaluation（实验与评估：拒绝报菜名，重分析与强归因）

这是绝大多数传统论文或低质 AI 生成稿件最容易翻车的重灾区。**审稿人自己会看表格里的数字，不需要作者在正文里机械地把表里的每一个单元格复述一遍（即“报菜名”）**。顶级论文的实验写作核心是：**挑代表性数据为佐证，重深层机理分析，把实证现象归因到有证据支持的机制；措辞的强度必须与证据的强度一致（见下方“归因证据阶梯”）。**

### 2.6.1 宏观 RQ 驱动与 Setup 四大块
- **RQ 统摄**：实验开篇必须显明列出 `RQ1–RQ5`，后续各小节直接对应（如 "§5.2 RQ1: Adaptability under Dynamic Drift"）。
- **Setup 模块化规范**：使用段首加粗小标题清晰划分四大块：
  - **Datasets**：数据集名称、数据量、划分方式（如 Dirichlet Non-IID 与 Pathological Non-IID，讲清分别模拟了何种真实异构分布）；
  - **Baselines**：经典基线与最新 SOTA，每种基线用 1 句话讲清其核心技术机理；
  - **Implementation Details**：硬件型号、深度学习框架、优化器类型、学习率、通信轮数、客户端参与率；
  - **Metrics**：评估指标定义（Accuracy, Convergence Speed, Variance Across Backbones, Drop Rate）。

### 2.6.2 实验结果段落黄金法则：“总—分—总”与机制映射
评测正文的每一个自然段，都必须严格遵守**“总—分—总”（Topic - Evidence - Mechanism Mapping）**三步逻辑：

```
+--------------------------------------------------------------------------+
|                     Evaluation 段落黄金法则: 总 - 分 - 归因              |
+--------------------------------------------------------------------------+
| 1. 首句 (Topic Sentence / 结论先行):                                      |
|    明确给出本段的核心实证结论，指明在什么场景下大幅超越了基线              |
|    (例: "The experimental comparisons demonstrate the superior           |
|    performance and stability of FedPE under dynamic data distributions.")|
|                                                                          |
| 2. 中间句 (Selective Evidence / 挑选代表性数据为佐证):                   |
|    绝不逐行读表！仅挑选最难的任务、最具杀伤力的极端数据或领先区间进行佐证  |
|    (例: "As shown in Table 1, FedPE achieves accuracy rates of 57.78%,   |
|    56.34%, and 53.59% on CIFAR-100, outperforming sub-optimal baselines  |
|    by 2.35%-5.18%, while maintaining over 95% on simpler datasets.")     |
|                                                                          |
| 3. 末句 (Mechanism Mapping / 归因到机制，措辞匹配证据强度):              |
|    解释为什么会有这一结果，点名具体组件或机制，并引用支持它的证据；      |
|    没有消融/对照证据时，只能写成假设（见下方“归因证据阶梯”）            |
|    (例: "Analysis suggests that DDAP is capable of rapid optimization,   |
|    providing accurate prompts for local models, while PKM effectively    |
|    suppresses catastrophic feature overwriting.")                        |
+--------------------------------------------------------------------------+
```

#### 归因证据阶梯（Attribution Evidence Ladder，MUST）

末句的归因措辞必须与手头证据的强度一致；**NEVER** 把事后解释写成“已证实的预测”。

| 证据 | 允许的措辞 | 示例 |
| :--- | :--- | :--- |
| **因果证据**：消融（去掉该组件后差距消失）、对推定原因的受控干预 | *is caused by*, *stems from*, *removing X eliminates* | *"Removing PKM erases 80% of the gap (Table 5), so the gain stems from its cross-round constraint."* |
| **相关证据**：探针、相关性、案例、可视化 | *is consistent with*, *suggests*, *coincides with* | *"The delayed emergence of safety features in the probes is consistent with this explanation."* |
| **无直接证据** | *we hypothesize that ...*，并说明如何检验；或干脆不写 | *"We hypothesize that ...; testing this requires ..."* |

- **NEVER** 使用 *proves / conclusively / confirms that / undoubtedly / definitively* 描述实验结论（`lint_paper.py` W305）；“证明”只用于形式化定理。
- 一条解释若在结果出来之后才提出，就不能称为“预测”；称为预测的，实验设计必须先于结果写明。
- 不支持假设的结果与支持它的结果同样要写出。

---

### 2.6.3 顶级实验深度分析的四大实战范式

以下四大范式直接来自前沿顶刊的实战技巧，能让实验章节立刻展现出资深学者的学术深度：

#### 范式 1：基线对比分析（Baseline Comparison）——抓难点与区间，重行为轨迹
- **反面教材（低质报菜名）**：“在数据集 A 上，基线 1 为 65%，基线 2 为 89%，我们的方法为 89.78%；在 40 客户端下，基线 1 为 64%……”（审稿人直呼头疼）。
- **正面范式（FedPE 典范）**：
  - 在大表中只抓**最复杂的挑战任务**（如 CIFAR-100）和**相对领先区间**（领先次优方法 2.35%–5.18%），其余简单任务用一句“在各基线均高于 95% 的任务上依然保持最优”带过；
  - 在收敛曲线（Convergence Curves）分析中，不逐轮报数，而是分析**行为轨迹（Behavioral Patterns）**：“基线在分布漂移时出现大幅震荡甚至遗忘断崖，而我们的方案呈现平滑连续的学习轨迹，这证实了 PKM 机制对历史知识的平滑保留能力”。

#### 范式 2：参数敏感性与拐点分析（Parameter Sensitivity & Trade-off）——讲透先升后降的物理本质
- **反面教材**：“当超参数设为 1 时准确率是 93%，设为 2 时是 97%，设为 4 时是 94%，所以 2 是最好的”。
- **正面范式（FedPE 典范）**：
  - 观察现象：随着卷积层数（或超参数）增加，系统性能呈现**“先上升后下降”**的倒 U 型趋势；
  - **剖析深层权衡机制（Trade-off Analysis）**：
    - *前期上升的原因*：层数适度增加增强了深层特征抽象能力（*progressive enhancement of deep feature abstraction*）；
    - *后期下降的原因*：网络过深导致参数量激增，引发过拟合，模型开始**“死记硬背训练样本中的噪声而非学习底层泛化规律”**（*memorize noise rather than learning underlying patterns*）；
  - **定论**：因此该参数取值正是“特征表达力”与“防过拟合风险”之间的最优工程平衡点。

#### 范式 3：模型结构鲁棒性与解耦分析（Architecture Invariance & Decoupling）——比方差与解耦能力
- **反面教材**：“我们在 ResNet 上取得了 55%，在 EfficientNet 上取得了 54%，都高于基线”。
- **正面范式（FedPE 典范）**：
  - **对比跨架构方差（Variance Across Backbones）**：我们的方法在更换主干网络时性能差异仅为 0.88%（*negligible variance*），而基线在换骨干网后精度剧烈滑坡高达 6.87%；
  - **机制升华（Decoupling Insight）**：这一巨大反差证明了我们的方案**“成功将分布自适应能力与特定骨干网络的特征提取过程进行了解耦”**（*decouples distribution adaptation from backbone-specific feature learning*）；
  - **双模块协同归因**：归因于 DDAP 是天然架构无关的（Architecture-agnostic），而 PKM 跨轮约束抑制了不同架构引起的梯度冲突。

#### 范式 4：两阶段受控动态抗压测试（Two-Phase Dynamic Stress Testing）——评估动态扰动下的衰减韧性
- **实验设计**：
  - **Phase I（稳定基线期，Rounds 1–100）**：各节点正常完整训练；
  - **Phase II（动态扰动期，Rounds 101–200）**：引入逼真的动态扰动（如每 10 轮随机屏蔽 10% 节点的 20% 数据）；
- **核心分析重点**：不只看绝对数值，重点看**“从 Phase I 到 Phase II 的性能衰减幅度（Performance Degradation / Drop Rate）”**——我们的方法衰减幅度极小（仅 0.47%），而所有基线出现 1.34%–4.19% 的严重滑坡。
- **归因**：这体现了系统面对扰动时的高弹性（Resilience），直接归因于自适应提示与历史记忆模块的协同运作。

---

## 2.6.4 Few-shot：同一组数据的两种写法

输入：Table 1（CIFAR-10 / CIFAR-100 × 3 种划分，FedPE 与 5 个基线），组件 DDAP（自适应提示）与 PKM（跨轮记忆约束）。

❌ **Bad（报菜名，无归因）**
> *On CIFAR-10, FedAvg achieves 65.21%, FedProx 66.03%, pFedPG 89.12%, and FedPE 89.78%. On CIFAR-100, FedAvg achieves 41.37%, FedProx 42.10%, pFedPG 52.41%, and FedPE 57.78%. Therefore, our method is the best.*

✅ **Good（总—分—归因）**
> *FedPE consistently outperforms all baselines under dynamic distributions, and its advantage widens as the task becomes harder. On CIFAR-100, it reaches 57.78%, 56.34%, and 53.59% across the three partitions, exceeding the second-best method by 2.35%–5.18%, while all methods stay above 95% on the simpler datasets. We attribute this gap to DDAP, which re-aligns local prompts to the shifted distribution within a few rounds, and to PKM, which penalizes abrupt parameter changes and thus suppresses catastrophic feature overwriting.*

要点：首句给结论；只挑最难任务的 2–3 个数字与领先区间；末句点名到具体组件与机制——这里用 *We attribute* 是因为消融实验（Table 4）中去掉任一组件都会让差距明显缩小；若没有这类证据，末句应改为 *This is consistent with ...* 或写成假设；数字全部来自 Table 1。
