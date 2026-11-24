# Related Work / Preliminaries & Problem Formulation

> 适用：相关工作、预备知识与问题建模。

## 2.2 Related Work（相关工作：三层递进漏斗与转折批判技巧）

Related Work 绝不是文献清单的简单罗列，其本质使命是**为本文方案的“独特性与不可替代性”构筑逻辑围墙**。

### 2.2.1 三层递进漏斗模型（The Three-Tier Funnel Model）
组织子小节时，推荐采用从宏观领域向本文核心技术交叉点逐步收拢的三层漏斗结构（以 FedPE 为例）：
1. **§2.1 目标宏观领域（Target Domain）**：如 *Personalized Federated Learning*（介绍宏观背景、已有主流范式及共同局限）；
2. **§2.2 核心支撑技术（Enabling Technology）**：如 *Prompt Learning*（从 NLP 预训练大模型迁移至参数高效微调的演化历程）；
3. **§2.3 交叉前沿领域（The Intersection Frontier）**：如 *Prompt-based Federated Learning*（两者结合的最新探索，直接切入本文待解的无人区）。

### 2.2.2 子节内部的“演进 $\to$ 分类学梳理 $\to$ 转折批判”三部曲
相关工作的每一个二级子节，都必须由以下三个逻辑层次构成：
- **第 1 层：技术演进脉络**：用简练语言梳理该领域从经典开山之作（如 FedAvg / Transformer）到近年前沿的发展轨迹；
- **第 2 层：分类学系统梳理（Taxonomy Organization）**：严禁按作者年份流水账陈列，必须按**技术路线分类归纳**。例如在 PFL 中梳理为：
  - *双层模型架构类（Two-tier models）*；
  - *类原型交互类（Class prototypes）*；
  - *语义正则化类（Semantic regularization）*；
  - *客户端聚类分析类（Client clustering）*；
  - *元学习小样本微调类（Meta-learning few-shot adaptation）*。
- **第 3 层：收尾的黄金转折批判句（The Transition / Gap Statement）**：每一个子节的末尾必须以一个**独立的转折批判段落**收尾，指出该类别所有方法的共同死穴，从而顺理成章地引出本文的切入点：
  - *子节末转折模板（来自 FedPE）*：*"Although the aforementioned methods have tailored personalized models on the client side, models that are tightly coupled with specific data distributions struggle to adapt to new distribution characteristics in dynamic scenarios."*

---

## 2.3 Preliminaries & Problem Formulation（预备知识：纯净环境与符号规范）

### 纯净环境原则（Strict Decoupling）
- **绝不在此处引入本文自研方法**：预备知识章节是为后续算法推演搭建纯净的舞台。严禁在该章节掺杂自身提出的算法名称、模块或技巧。
- **职责定位**：仅定义审稿人达成共识的**物理环境**、**数学符号系统**、以及**通用基线优化目标**。

### 标准三元组建模结构
1. **环境与符号定义（System Setup & Notation）**：
   - 清晰定义参与方集合（$N$ 个客户端，中心协调服务器）；
   - 数据集符号：全集 $D$，本地私有集 $D_i$，样本规模 $|D_i|$；
   - 空间定义：特征空间 $\mathcal{X}$、标签空间 $\mathcal{Y}$，客户端局部异构分布 $p_i$。
2. **常规优化目标（Standard Optimization Formulation）**：
   - 给定标准损失函数 $\ell(w; x, y)$，形式化写出传统全局模型的优化目标：
     $$\min_{w} \mathcal{L}(w) = \sum_{i=1}^N \frac{|D_i|}{|D|} \mathcal{L}_i(w)$$
3. **前沿/个性化优化目标（PFL Formulation）**：
   - 形式化推导出个性化设置下的联合优化方程：
     $$\min_{\{w_i\}_{i=1}^N} \sum_{i=1}^N \mathcal{L}_i(w_i)$$
   - 点明该经典目标是在“静态数据分布”假设下成立，为第 4 节切入“动态数据适应”埋下严谨的数学伏笔。
