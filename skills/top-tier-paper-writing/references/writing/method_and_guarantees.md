# Method / Defense / Theoretical Guarantees

> 适用：方法论、系统设计、防御机制与理论保证章节。

## 2.4 Method / System Architecture（方法论：算法总览与三层解构范式）

### 宏观架构组织
- **§4.1 架构图（Figure 1）与主算法（Algorithm 1）统摄**：
  - 开篇第一小节统揽全局：用 1 个全景流程图（标注清楚客户端与服务端的交互边界）；
  - 提供标准的执行伪代码（Algorithm 1），清晰划分为 `Server Executes` 与 `Client Executes`；
  - **核心细节**：伪代码中的关键操作行（如 Line 14: 一步自适应更新，Line 15: 元优化更新），必须在正文中明确标出对应的数学公式编号。

### 技术子模块的三层解构范式（直觉目标 $\to$ 形式建模 $\to$ 优化机理）
每一个算法子模块（如 §4.2 DDAP, §4.3 PKM），都必须严格遵循以下三层结构展开，确保内容**通俗易懂却不失数学严谨性**：

```
+--------------------------------------------------------------------------+
|                  Method 模块展开的三层解构范式                           |
+--------------------------------------------------------------------------+
| 1. 直觉目标 (Intuitive Goal):                                            |
|    用直白、通俗的工程语言阐述该模块直觉上要解决什么痛点、达到什么目标     |
|    (例: "Intuitively, DDAP strives to seek optimal initialization       |
|    parameters that facilitate rapid convergence under new distributions")|
|                                                                          |
| 2. 形式化建模 (Formal Mathematical Formulation):                          |
|    给出规范的前向数学公式，清晰定义输入张量、算子结构、中间特征与输出维度 |
|    - 公式 1: 提示词生成 p_k^e = Pr(X_k^e)                                |
|    - 公式 2: 特征抽取 f_k^e = Encoder(X_k^e)                             |
|    - 公式 3: 拼接推理 g_k^e = Header([f_k^e, p_k^e])                     |
|                                                                          |
| 3. 工作与优化机理 (Working Mechanism & Optimization Flow):                |
|    拆解执行阶段 (Stage 1: Fine-tuning 与 Stage 2: Meta-optimization),     |
|    详细交代前向计算与梯度更新策略，明确“更新哪些参数、冻结哪些参数”     |
+--------------------------------------------------------------------------+
```

### 动态自适应因子的物理设计原则
- 在设计正则项或损失函数时，避免引入纯人工经验常量。
- **范式示范（来自 FedPE）**：
  $$\mathcal{L}(w) = \ell(w; x, y) + \lambda(1 - p(w)) \Omega(\phi, \phi^{prev})$$
  - 正文中必须阐明动态自适应因子 $\lambda(1 - p(w))$ 的物理直觉：$p(w)$ 表示当前模型的瞬时准确率。当模型精度较低（处于分布突变初期）时，$(1-p(w))$ 增大，系统自动施加极强的正则化约束，强行保护历史特征记忆；当模型适应良好、精度回升时，正则项自动衰减，赋予局部模型充分的自由度去探索新分布。这种设计能极大提升审稿人对方法技术含金量的评价。

### 超参数隔离铁律
- **方法论中绝对不出现具体超参数值**：严禁在 Method 中写“我们设置学习率为 0.005，迭代 200 轮，卷积核深度为 2”。这些具体数字必须统一移入 §Evaluation Setup 和附录。
- **正文只阐述参数的控制与物理行为**。

---

## 2.5 Defense / Security & Theoretical Guarantees（防御机制与理论保证）

### 决策论证型段落结构（Design Decisions & Rationale）
每个段落阐明**一个核心设计决策及其不可替代的理由**：
- **段首小标题优秀范式**：
  - *Why the gate always measures $d_T$*：先指明更廉价的轻量方案存在致命盲区，再论证度量 $d_T$ 的不可替代性；
  - *Separating fact changes from rule changes*：论述如何利用同一次查询搭便车（piggybacking），以零额外开销解耦规则与事实；
  - *Escalating what the model cannot decide*：论述系统弹性，将处于置信度边界上的样本安全升级给人工审核。

### 设计目标 G1–G4 与基线对比矩阵
1. 在正文开头形式化提出系统设计的四大支柱目标：**G1: 完整性保证**、**G2: 系统可用性**、**G3: 计算开销**、**G4: 易部署性**；
2. 构造一张横向对比表，用 ✓ / ✗ 符号将本方案与已有主流方案在 G1–G4 上全面对比，正文后续论述持续引用 `(G1)`–`(G4)` 闭环印证。

### 形式化理论保证（Theoretical Guarantees）四步论述结构
1. **证明目标与现实价值**：开宗明义阐明定理要保障的核心性质与工程意义；
2. **形式化假设前提（Assumptions）**：清晰枚举假设前提（"First ... Second ..."）；
3. **命题与证明摘要（Proposition & Proof Sketch）**：给出严密数学表达，长篇推导标注指向附录；
4. **防护边界（What the guarantee does NOT cover）**：主动交代该保证不覆盖的外围极端场景，展现学术严谨性。
