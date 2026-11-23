# 通用计算机顶会/顶刊论文写作规范与段落解剖指南 (Universal CS Paper Writing Specification)

[![Domain: Computer Science](https://img.shields.io/badge/Domain-Computer%20Science%20(AI%20%7C%20Security%20%7C%20Systems)-blue.svg)]()
[![Target: Top-tier Conf & Trans](https://img.shields.io/badge/Target-CCF--A%20%2F%20IEEE%20Trans%20%2F%20ACM-brightgreen.svg)]()
[![Focus: Full Lifecycle Anatomy](https://img.shields.io/badge/Focus-Full%20Lifecycle%20Section%20%26%20Paragraph%20Anatomy-orange.svg)]()

> 本指南综合提炼自高水平计算机体系结构、网络安全、人工智能与分布式系统顶会（如 IEEE S&P）及权威顶级期刊（如 IEEE Transactions, compsoc 模板，以及 Elsevier 权威网络期刊，如 FedPE 顶刊实战案例）的真实写作、审稿与改稿经验。
> 
> 旨在从**“发表过多篇顶会/顶刊的优秀博士生与资深审稿人”**视角，建立一套标准化的**通用计算机学术论文写作全景指南**：系统拆解论文从 Title、Abstract 到 Conclusion 的**每一部分的宏观逻辑架构**、**微观段落展开方式（每一段该写什么、怎么写、如何过渡）**，全面覆盖：
> 1. **引言的“双挑战—双案例—双直觉”对称推进法**；
> 2. **相关工作的“三层递进漏斗”与“转折批判”技巧**；
> 3. **预备知识与问题建模的“符号纯净性”原则**；
> 4. **方法论的“系统总览—直觉目标—形式建模—优化机理”三层解构范式**；
> 5. **实验章节“拒绝报菜名堆数据，重深层机理分析与组件归因”的四大实战范式**；
> 6. **讨论与结论的高维度收束与精准未来展望**。

---

## 目录（Table of Contents）

- [一、核心原则与学术诚信（Core Philosophy）](#一核心原则与学术诚信core-philosophy)
  - [1.1 表层流畅，底层严谨（Narrative Flow vs. Deep Rigor）](#11-表层流畅底层严谨narrative-flow-vs-deep-rigor)
  - [1.2 诚实优先于漂亮（Honesty over Prettiness）](#12-诚实优先于漂亮honesty-over-prettiness)
  - [1.3 增补实验后的全局动态回溯（Global Backward Consistency）](#13-增补实验后的全局动态回溯global-backward-consistency)
  - [1.4 贯穿实例与源头核验（Single Source of Truth）](#14-贯穿实例与源头核验single-source-of-truth)
- [二、各章节宏观结构与段落微观解剖（Section & Paragraph Anatomy）](#二各章节宏观结构与段落微观解剖section--paragraph-anatomy)
  - [2.0 Title & Abstract（标题与摘要：对称性与黄金骨架）](#20-title--abstract标题与摘要对称性与黄金骨架)
  - [2.1 Introduction（引言：7 步递进叙事流、真实案例与镜像直觉）](#21-introduction引言7-步递进叙事流真实案例与镜像直觉)
  - [2.2 Related Work（相关工作：三层递进漏斗与转折批判技巧）](#22-related-work相关工作三层递进漏斗与转折批判技巧)
  - [2.3 Preliminaries & Problem Formulation（预备知识：纯净环境与符号规范）](#23-preliminaries--problem-formulation预备知识纯净环境与符号规范)
  - [2.4 Method / System Architecture（方法论：算法总览与三层解构范式）](#24-method--system-architecture方法论算法总览与三层解构范式)
  - [2.5 Defense / Security & Theoretical Guarantees（防御机制与理论保证）](#25-defense--security--theoretical-guarantees防御机制与理论保证)
  - [2.6 Evaluation（实验与评估：拒绝报菜名，重分析与强归因）](#26-evaluation实验与评估拒绝报菜名重分析与强归因)
    - [2.6.1 宏观 RQ 驱动与 Setup 四大块](#261-宏观-rq-驱动与-setup-四大块)
    - [2.6.2 实验结果段落黄金法则：“总—分—总”与机制映射](#262-实验结果段落黄金法则总分总与机制映射)
    - [2.6.3 顶级实验深度分析的四大实战范式（对比、拐点、解耦、多阶段抗压）](#263-顶级实验深度分析的四大实战范式对比拐点解耦多阶段抗压)
    - [2.6.4 顶会/顶刊机制映射经典句式库（Mechanism Mapping Sentence Bank）](#264-顶会顶刊机制映射经典句式库mechanism-mapping-sentence-bank)
  - [2.7 Discussion（深度讨论：回答 Why，绝不重复 What）](#27-discussion深度讨论回答-why绝不重复-what)
  - [2.8 Conclusion（结论：终局定论与精准未来展望）](#28-conclusion结论终局定论与精准未来展望)
  - [2.9 Ethics Considerations & Responsible Disclosure（伦理考量与披露）](#29-ethics-considerations--responsible-disclosure伦理考量与披露)
  - [2.10 论文信息架构速查表：细节该放哪里（Where Details Belong）](#210-论文信息架构速查表细节该放哪里where-details-belong)
- [三、段落与句子级学术微雕规范（Sentence Crafting & Academic Diction）](#三段落与句子级学术微雕规范sentence-crafting--academic-diction)
  - [3.1 明确主语与严谨修饰](#31-明确主语与严谨修饰)
  - [3.2 极简原则与段落节律（Sentence Economy）](#32-极简原则与段落节律sentence-economy)
  - [3.3 语域正式度与术语全文统一](#33-语域正式度与术语全文统一)
  - [3.4 格式习惯与消除防御性限定](#34-格式习惯与消除防御性限定)
- [四、图表视觉传达与双栏排版布局规范（Visuals & Typesetting）](#四图表视觉传达与双栏排版布局规范visuals--typesetting)
  - [4.1 图的视觉设计与 Caption 规范](#41-图的视觉设计与-caption-规范)
  - [4.2 表格自动化规范与指标呈现](#42-表格自动化规范与指标呈现)
  - [4.3 双栏 LaTeX 浮动体三大硬性黄金法则](#43-双栏-latex-浮动体三大硬性黄金法则)
  - [4.4 浮动体四级调试阶梯与版面补偿技巧](#44-浮动体四级调试阶梯与版面补偿技巧)
- [五、参考文献规范与多源校验（Bibliography Verification）](#五参考文献规范与多源校验bibliography-verification)
  - [5.1 多源核验与常见避坑清单](#51-多源核验与常见避坑清单)
  - [5.2 格式规范与战略引用](#52-格式规范与战略引用)

---

## 一、核心原则与学术诚信（Core Philosophy）

### 1.1 表层流畅，底层严谨（Narrative Flow vs. Deep Rigor）
- **叙事主线极简化**：正文主线叙事要让审稿人一口气读懂三个核心问题：*为什么难（Why hard）*、*怎么解决（How to solve）*、*效果究竟如何（How well it works）*。正文中严禁掺杂过多琐碎的支线防御与边缘说明。
- **严谨性细节下沉**：审稿人关注的严谨性细节（样本量估算、模型与工具版本、数据清洗规则、统计显著性检验、理论保守下界的推导细节）坚决放进**表注（Table Notes）**、**实验设置（Setup）**、**有效性论证（Validity）**和**附录（Appendix）**。审稿人起疑翻过去就能看到，但不打断主线阅读。
- **正文信息信噪比**：正文中的每一句话都必须有明确信息增量。如果一句话在正文别处已出现过、只是机械重述表格里的数值，或者仅仅是在防御性地限定范围，必须果断删减或移走。

### 1.2 诚实优先于漂亮（Honesty over Prettiness）
- **杜绝数据不支持的推论**：即使某个结论听起来更具颠覆性，只要数据不支持就坚决不写。例如消融实验若显示 feedback 与 exploration 探索项增益微弱，不可粉饰为“每个组件都发挥了关键作用”，而应诚实定性为“核心机制占主导，外围搜索无需繁琐精调即可达到强劲效果”。这反而体现了系统的鲁棒性与高实用价值。
- **直面基线优势，多维度对比**：当基线方法在核心准确率上与我们极为接近甚至在个别点占优时，绝不回避隐瞒。应当指出我们在其他维度的综合优势，并给出真实可复核的区间（例如："its FPR is 7.2–19.2% against 2.2–12.9% for our method"）。
- **最坏情况（Worst-case）与统计分布呈现**：分别列出不同数据集和对抗环境下的最坏情况准确率（Worst-case accuracy），坚决摒弃仅用最优平均值掩盖脆弱性的做法；明确标注结论成立的条件（例如：“在最差情况下”、“非 IID 分布”、“三个随机种子取平均”）。

### 1.3 增补实验后的全局动态回溯（Global Backward Consistency）
任何增补实验都可能产生蝴蝶效应，导致早先章节的理论前提、论断或威胁模型失效。每加一组实验，必须以批判性眼光从头通读并全局检索全文：
- **检查清单**：
  1. **引言与贡献列表**：贡献范围是否需要重述或修正？
  2. **威胁模型（Threat Model）**：增补实验是否突破了原有的假设边界？（如：原本写“恶意上传必然被量化”，后增补自选格点攻击，必须推翻改写）。
  3. **理论边界与数学命题**：理论结论必须随实验适用范围同步扩展（如：补充攻击实验后，需在命题后追加证明引申，使理论检测极限同样覆盖新攻击）。
  4. **全文字符串与核心数字**：摘要、引言、正文、结论与 README 中的核心数字（如 4.7%, 8.7–45.1%, 9.3 ms）必须全局核对。修改一处数字，必须全局搜索替换。

### 1.4 贯穿实例与源头核验（Single Source of Truth）
- **贯穿示例必须源自真实实验日志**：引言中的运行示例（Running Example）、关键数值必须从原始实验结果文件（Log / PKL / JSON）中核实定位。
  - *血泪教训*：论文中的 Running Example 经回溯核实，其实是“唯一落在边界上被 Gate 升级给人工审核（Escalated to human）”的样本，而非被系统硬性“拦截”的样本。若作者想当然写成“被系统成功拦截”，一旦审稿人按图索骥复现核对，将成为不可挽回的学术硬伤。

---

## 二、各章节宏观结构与段落微观解剖（Section & Paragraph Anatomy）

### 2.0 Title & Abstract（标题与摘要：对称性与黄金骨架）

#### 标题设计规范
- **命名范式**：推荐采用两段式结构——`[系统/框架名]: [核心机制或解决的问题] in/for [具体领域/对象]`，或者 `[动名词短语]: [达成的核心保证/解决的痛点]`。
  - *范例*：`FedPE: A Prompt-Enhanced Personalized Federated Learning Framework for Dynamic Data Adaptation`
  - *范例*：`LEVER: Securing Typed Decision Gates Against Framing Attacks`
- **避免假大空**：避免使用 *"A Novel Approach..."*、*"Study on..."* 等毫无信息量的空泛词。系统名使用全大写或首字母大写正体。

#### 摘要的 5 句黄金骨架（150–250 词）
摘要是论文的微型缩影，必须严格由 5 个逻辑分句/小层次构成，且必须呈现出**挑战与解决方案的精确对称性**：

```
+--------------------------------------------------------------------------+
|                             Abstract 黄金骨架                            |
+--------------------------------------------------------------------------+
| 句 1: 背景与高价值场景 (Background: Cloud-edge / FL significance)         |
| 句 2: 常规机制与一般痛点 (General Gap: Data heterogeneity / Non-IID)     |
| 句 3: 已有 SOTA 的成就与残留挑战 (SOTA Achievement & Unsolved Challenges)|
|       - 挑战 1: 静态假设无法适应动态分布漂移 (Dynamic distribution drift)|
|       - 挑战 2: 随机出入导致的历史知识遗忘与特征稀释 (Feature dilution)   |
| 句 4: 本文方案与核心组件对称响应 (Proposed Method & Symmetrical Modules)  |
|       - 响应 1: 提出 DDAP 模块生成对齐提示词，实现小样本快速自适应        |
|       - 响应 2: 提出 PKM 机制约束跨轮参数演化，锁定历史记忆抗遗忘        |
| 句 5: 决定性实验结果与实用价值 (Decisive Quantitative Results & Impact)    |
+--------------------------------------------------------------------------+
```

- **时态约定**：Abstract 是“预告”，介绍自身工作统一使用**一般现在时**（"We propose FedPE...", "Experimental results demonstrate that..."）。
- **避坑**：不要在摘要中放背景引用，不要放未定义的内部缩写，核心指标给出 1–2 个最具杀伤力的跨度区间即可。

---

### 2.1 Introduction（引言：7 步递进叙事流、真实案例与镜像直觉）

Introduction 绝非背景介绍，而是一场逻辑严密、步步为营的学术论辩。推荐经典的 **7 步递进叙事流（7-step Narrative Progression）**，对应正文的前 5–7 个段落：

#### 第 1 段：背景、应用场景与直观运行实例（Context & Running Example）
- **段落功能**：迅速切入高价值应用场景，用一个具象化痛点抓住审稿人。
- **段落内部结构**：
  - *第 1 句*：界定核心研究场景（如“在边缘计算与联邦学习系统中……”）；
  - *第 2–3 句*：阐述系统的常规期望工作流程；
  - *第 4–5 句（核心）*：**直接引出 Figure 1 的贯穿实例（Running Example）**，直观展示即使在最简单或最具代表性的输入下，现有系统也会出现反直觉的崩溃、过拟合或安全漏洞。

#### 第 2 段：已有工作的本质缺陷与量化实证（SOTA Limitations with Quantified Evidence）
- **段落功能**：证明这不是偶发个案，而是现有前沿方法普遍存在的系统性漏洞。
- **段落内部结构**：
  - *第 1 句*：总述已有方案（如基于超网络、元学习或提示词约束等）试图解决该问题；
  - *第 2–3 句*：指出其本质盲区（如静态数据分布假设在动态漂移场景下失效）；
  - *第 4 句（杀手锏）*：**给出压倒性的定量统计证据**（例如：“最强基线在面对动态漂移时历史数据识别率暴跌超过 40%”），用硬数据彻底否定现有方案。

#### 第 3 段：双技术挑战与真实领域案例映射（Two Challenges with Domain Real-World Cases）
- **段落功能**：向审稿人证明“为什么这个问题极难解决，为什么不能套用现成轮子”。
- **段落内部结构（FedPE 典范范式）**：
  - *引导句*：总述尽管已有方法取得了进展，但仍面临两个本质挑战（*"Despite significant improvements, two critical challenges remain."*）；
  - *Challenge 1 + 真实案例*：常规方法假设数据分布静态恒定，无法适应动态漂移。**立即映射到具体现实案例**（例如：“在医疗领域，患者跨医院转诊导致接收机构的数据规模、特征维度与病理分布随时间发生动态漂移”）；
  - *Challenge 2 + 真实案例*：边缘数据随机接入与退出导致历史特征被稀释。**立即映射到具体实证案例**（例如：“在图像分类任务中，模型对新涌现样本保持高精度，但对暂时退出历史数据的识别性能发生断崖式暴跌”）。

#### 第 4 段：直觉解法段落——与第 3 段严格对称的“双直觉响应”（Symmetrical Intuitive Solutions）
- **段落功能**：在给出复杂的数学公式前，先用纯人类直觉证明“我们的解法为什么天然合理”。
- **段落内部结构（首尾句与第 3 段 1-to-1 镜像对齐）**：
  - *引导句*：*"Intuitively, we propose a novel framework for dynamic data distributions."*
  - *直觉响应 1（呼应 Challenge 1）*：针对新分布失配问题，提出不重训主干模型，而是**提供辅助提示词（Supplemental Prompts）**引导模型低成本对齐新分布；
  - *直觉响应 2（呼应 Challenge 2）*：针对历史特征稀释，提出**跨轮知识记忆约束**，在参数更新中强制锁定历史数据表征，确保历史节点重连时秒级复苏。

#### 第 5 段：本文方法架构与组件挑战映射（Method Summary & Component Mapping）
- **段落功能**：正式介绍自研系统架构名，并完成模块与挑战的闭环绑定。
- **段落内部结构**：
  - *第 1 句*：隆重提出自研系统（如 FedPE / LEVER）；
  - *第 2–4 句*：逐一拆解核心组件（如 DDAP 应对 Challenge 1，PKM 机制应对 Challenge 2），并在句中显式打上标签 `(C1)`、`(C2)`。

#### 第 6 段：防御机制/系统扩展与形式化保证（Defense / Extension & Guarantees）
- **段落功能**：展示系统闭环能力（若有攻防双向或系统级扩展贡献）。
- **段落内部结构**：使用 *"We further propose..."* 独立引出防御机制或理论模型，简述形式化边界，交代该机制为大规模工业落地提供了坚实保证。

#### 第 7 段：贡献列表（Contributions List）
- **段落功能**：审稿人打分的最直接依据。采用四条精炼条目：
  - **(1) 现象与问题发现**：发现了什么隐蔽漏洞、经验缺陷或理论边界；
  - **(2) 新型核心方法**：提出了什么全新机理的方法架构（如 DDAP）；
  - **(3) 理论约束与保障机制**：提出了什么保障机制与形式化证明（如 PKM 记忆正则项）；
  - **(4) 决定性评测结果**：在哪些真实基准上取得了什么突破性指标（给出最硬核的 1–2 个代表性数字）。

---

### 2.2 Related Work（相关工作：三层递进漏斗与转折批判技巧）

Related Work 绝不是文献清单的简单罗列，其本质使命是**为本文方案的“独特性与不可替代性”构筑逻辑围墙**。

#### 2.2.1 三层递进漏斗模型（The Three-Tier Funnel Model）
组织子小节时，推荐采用从宏观领域向本文核心技术交叉点逐步收拢的三层漏斗结构（以 FedPE 为例）：
1. **§2.1 目标宏观领域（Target Domain）**：如 *Personalized Federated Learning*（介绍宏观背景、已有主流范式及共同局限）；
2. **§2.2 核心支撑技术（Enabling Technology）**：如 *Prompt Learning*（从 NLP 预训练大模型迁移至参数高效微调的演化历程）；
3. **§2.3 交叉前沿领域（The Intersection Frontier）**：如 *Prompt-based Federated Learning*（两者结合的最新探索，直接切入本文待解的无人区）。

#### 2.2.2 子节内部的“演进 $\to$ 分类学梳理 $\to$ 转折批判”三部曲
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

### 2.3 Preliminaries & Problem Formulation（预备知识：纯净环境与符号规范）

#### 纯净环境原则（Strict Decoupling）
- **绝不在此处引入本文自研方法**：预备知识章节是为后续算法推演搭建纯净的舞台。严禁在该章节掺杂自身提出的算法名称、模块或技巧。
- **职责定位**：仅定义审稿人达成共识的**物理环境**、**数学符号系统**、以及**通用基线优化目标**。

#### 标准三元组建模结构
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

---

### 2.4 Method / System Architecture（方法论：算法总览与三层解构范式）

#### 宏观架构组织
- **§4.1 架构图（Figure 1）与主算法（Algorithm 1）统摄**：
  - 开篇第一小节统揽全局：用 1 个全景流程图（标注清楚客户端与服务端的交互边界）；
  - 提供标准的执行伪代码（Algorithm 1），清晰划分为 `Server Executes` 与 `Client Executes`；
  - **核心细节**：伪代码中的关键操作行（如 Line 14: 一步自适应更新，Line 15: 元优化更新），必须在正文中明确标出对应的数学公式编号。

#### 技术子模块的三层解构范式（直觉目标 $\to$ 形式建模 $\to$ 优化机理）
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

#### 动态自适应因子的物理设计原则
- 在设计正则项或损失函数时，避免引入纯人工经验常量。
- **范式示范（来自 FedPE）**：
  $$\mathcal{L}(w) = \ell(w; x, y) + \lambda(1 - p(w)) \Omega(\phi, \phi^{prev})$$
  - 正文中必须阐明动态自适应因子 $\lambda(1 - p(w))$ 的物理直觉：$p(w)$ 表示当前模型的瞬时准确率。当模型精度较低（处于分布突变初期）时，$(1-p(w))$ 增大，系统自动施加极强的正则化约束，强行保护历史特征记忆；当模型适应良好、精度回升时，正则项自动衰减，赋予局部模型充分的自由度去探索新分布。这种设计能极大提升审稿人对方法技术含金量的评价。

#### 超参数隔离铁律
- **方法论中绝对不出现具体超参数值**：严禁在 Method 中写“我们设置学习率为 0.005，迭代 200 轮，卷积核深度为 2”。这些具体数字必须统一移入 §Evaluation Setup 和附录。
- **正文只阐述参数的控制与物理行为**。

---

### 2.5 Defense / Security & Theoretical Guarantees（防御机制与理论保证）

#### 决策论证型段落结构（Design Decisions & Rationale）
每个段落阐明**一个核心设计决策及其不可替代的理由**：
- **段首小标题优秀范式**：
  - *Why the gate always measures $d_T$*：先指明更廉价的轻量方案存在致命盲区，再论证度量 $d_T$ 的不可替代性；
  - *Separating fact changes from rule changes*：论述如何利用同一次查询搭便车（piggybacking），以零额外开销解耦规则与事实；
  - *Escalating what the model cannot decide*：论述系统弹性，将处于置信度边界上的样本安全升级给人工审核。

#### 设计目标 G1–G4 与基线对比矩阵
1. 在正文开头形式化提出系统设计的四大支柱目标：**G1: 完整性保证**、**G2: 系统可用性**、**G3: 计算开销**、**G4: 易部署性**；
2. 构造一张横向对比表，用 ✓ / ✗ 符号将本方案与已有主流方案在 G1–G4 上全面对比，正文后续论述持续引用 `(G1)`–`(G4)` 闭环印证。

#### 形式化理论保证（Theoretical Guarantees）四步论述结构
1. **证明目标与现实价值**：开宗明义阐明定理要保障的核心性质与工程意义；
2. **形式化假设前提（Assumptions）**：清晰枚举假设前提（"First ... Second ..."）；
3. **命题与证明摘要（Proposition & Proof Sketch）**：给出严密数学表达，长篇推导标注指向附录；
4. **防护边界（What the guarantee does NOT cover）**：主动交代该保证不覆盖的外围极端场景，展现学术严谨性。

---

### 2.6 Evaluation（实验与评估：拒绝报菜名，重分析与强归因）

这是绝大多数传统论文或低质 AI 生成稿件最容易翻车的重灾区。**审稿人自己会看表格里的数字，不需要作者在正文里机械地把表里的每一个单元格复述一遍（即“报菜名”）**。顶级论文的实验写作核心是：**挑代表性数据为佐证，重深层机理分析，强行将实证现象映射回自研方法的具体组件！**

#### 2.6.1 宏观 RQ 驱动与 Setup 四大块
- **RQ 统摄**：实验开篇必须显明列出 `RQ1–RQ5`，后续各小节直接对应（如 "§5.2 RQ1: Adaptability under Dynamic Drift"）。
- **Setup 模块化规范**：使用段首加粗小标题清晰划分四大块：
  - **Datasets**：数据集名称、数据量、划分方式（如 Dirichlet Non-IID 与 Pathological Non-IID，讲清分别模拟了何种真实异构分布）；
  - **Baselines**：经典基线与最新 SOTA，每种基线用 1 句话讲清其核心技术机理；
  - **Implementation Details**：硬件型号、深度学习框架、优化器类型、学习率、通信轮数、客户端参与率；
  - **Metrics**：评估指标定义（Accuracy, Convergence Speed, Variance Across Backbones, Drop Rate）。

#### 2.6.2 实验结果段落黄金法则：“总—分—总”与机制映射
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
| 3. 末句 (Mechanism Mapping / 强行归因到自研方法组件):                    |
|    深度解释为什么会有这一结果，必须点名映射到自研方法的特定机制或数学算子  |
|    (例: "Analysis suggests that DDAP is capable of rapid optimization,   |
|    providing accurate prompts for local models, while PKM effectively    |
|    suppresses catastrophic feature overwriting.")                        |
+--------------------------------------------------------------------------+
```

---

#### 2.6.3 顶级实验深度分析的四大实战范式

以下四大范式直接来自前沿顶刊的实战技巧，能让实验章节立刻展现出资深学者的学术深度：

##### 范式 1：基线对比分析（Baseline Comparison）——抓难点与区间，重行为轨迹
- **反面教材（低质报菜名）**：“在数据集 A 上，基线 1 为 65%，基线 2 为 89%，我们的方法为 89.78%；在 40 客户端下，基线 1 为 64%……”（审稿人直呼头疼）。
- **正面范式（FedPE 典范）**：
  - 在大表中只抓**最复杂的挑战任务**（如 CIFAR-100）和**相对领先区间**（领先次优方法 2.35%–5.18%），其余简单任务用一句“在各基线均高于 95% 的任务上依然保持最优”带过；
  - 在收敛曲线（Convergence Curves）分析中，不逐轮报数，而是分析**行为轨迹（Behavioral Patterns）**：“基线在分布漂移时出现大幅震荡甚至遗忘断崖，而我们的方案呈现平滑连续的学习轨迹，这证实了 PKM 机制对历史知识的平滑保留能力”。

##### 范式 2：参数敏感性与拐点分析（Parameter Sensitivity & Trade-off）——讲透先升后降的物理本质
- **反面教材**：“当超参数设为 1 时准确率是 93%，设为 2 时是 97%，设为 4 时是 94%，所以 2 是最好的”。
- **正面范式（FedPE 典范）**：
  - 观察现象：随着卷积层数（或超参数）增加，系统性能呈现**“先上升后下降”**的倒 U 型趋势；
  - **剖析深层权衡机制（Trade-off Analysis）**：
    - *前期上升的原因*：层数适度增加增强了深层特征抽象能力（*progressive enhancement of deep feature abstraction*）；
    - *后期下降的原因*：网络过深导致参数量激增，引发过拟合，模型开始**“死记硬背训练样本中的噪声而非学习底层泛化规律”**（*memorize noise rather than learning underlying patterns*）；
  - **定论**：因此该参数取值正是“特征表达力”与“防过拟合风险”之间的最优工程平衡点。

##### 范式 3：模型结构鲁棒性与解耦分析（Architecture Invariance & Decoupling）——比方差与解耦能力
- **反面教材**：“我们在 ResNet 上取得了 55%，在 EfficientNet 上取得了 54%，都高于基线”。
- **正面范式（FedPE 典范）**：
  - **对比跨架构方差（Variance Across Backbones）**：我们的方法在更换主干网络时性能差异仅为 0.88%（*negligible variance*），而基线在换骨干网后精度剧烈滑坡高达 6.87%；
  - **机制升华（Decoupling Insight）**：这一巨大反差证明了我们的方案**“成功将分布自适应能力与特定骨干网络的特征提取过程进行了解耦”**（*decouples distribution adaptation from backbone-specific feature learning*）；
  - **双模块协同归因**：归因于 DDAP 是天然架构无关的（Architecture-agnostic），而 PKM 跨轮约束抑制了不同架构引起的梯度冲突。

##### 范式 4：两阶段受控动态抗压测试（Two-Phase Dynamic Stress Testing）——评估动态扰动下的衰减韧性
- **实验设计**：
  - **Phase I（稳定基线期，Rounds 1–100）**：各节点正常完整训练；
  - **Phase II（动态扰动期，Rounds 101–200）**：引入逼真的动态扰动（如每 10 轮随机屏蔽 10% 节点的 20% 数据）；
- **核心分析重点**：不只看绝对数值，重点看**“从 Phase I 到 Phase II 的性能衰减幅度（Performance Degradation / Drop Rate）”**——我们的方法衰减幅度极小（仅 0.47%），而所有基线出现 1.34%–4.19% 的严重滑坡。
- **归因**：这体现了系统面对扰动时的高弹性（Resilience），直接归因于自适应提示与历史记忆模块的协同运作。

---

#### 2.6.4 顶会/顶刊机制映射经典句式库（Mechanism Mapping Sentence Bank）

在撰写实验分析时，直接熟练运用以下经典的“现象 $\to$ 归因 $\to$ 机制”学术句式：

1. **核心组件直接归因**：
   - *"The superior performance of [Method] can be primarily attributed to [Component A]'s ability to [action], which effectively mitigates [challenge]."*
   - *"Analysis suggests that [Component A] is capable of [action], providing [benefit] that substantially enhances the adaptability to [scenario]."*
2. **多组件协同效应归因**：
   - *"The clear advantage in [metric] stems from the synergistic interactions between [Component A] and [Component B]: the former enables [action 1], while the latter enforces [action 2]."*
   - *"The well-separated semantic clusters in Fig. 5 highlight the combined effect of rapid adaptation guided by [Component A] and parameter continuity preserved by [Component B]."*
3. **架构解耦与不变性归因**：
   - *"The negligible performance variance across distinct backbone architectures underscores the capability of [Method] to decouple [process 1] from [process 2]."*
   - *"Unlike existing methods whose performance is contingent upon specific structural priors, [Method] is inherently architecture-agnostic."*
4. **与基线行为差异的因果对比**：
   - *"While baselines exhibit a pronounced tendency towards catastrophic forgetting during distribution shifts, [Method] maintains a coherent learning trajectory, attributable to [mathematical mechanism]."*
   - *"This disparity indicates that simply applying [baseline approach] fails to handle [phenomenon], whereas our [specific mechanism] successfully establishes a robust decision boundary."*

---

### 2.7 Discussion（深度讨论：回答 Why，绝不重复 What）

Discussion 篇幅控制在 0.5–1 页，其核心使命是**回答 Why，绝不重复 What**。优秀 Discussion 由以下 5 个结构化段落构成：

1. **深层机理本质（Why It Works）**：剥离具体的实验数字，从科学原理角度揭示为什么该方法能攻破/守住系统（例如：“类型化输出关闭了指令注入通道，但留下了语义解释空间；本方案正是利用了语义空间的不确定性”）。
2. **可迁移的设计原则（Transferable Design Principles）**：提炼出超越本篇论文、同行能够跨领域复用的系统架构原则（例如：“Defend on provenance, not on content”）。
3. **放松威胁模型与自适应攻防（Relaxing Assumptions & Adaptive Adversary）**：主动探讨核心假设若被打破系统会怎样，以及**彻底知晓本防御机制的强自适应攻击者**最多能做到什么程度，证明系统在极限条件下的抗压底线。
4. **更广泛的影响（Broader Impact）**：论述方法如何泛化推广至大模型评判（LLM-as-judge）、自治 Agent 工具审批等相邻高价值领域。
5. **极简、精准的局限性界定（Limitations）**：用客观冷静的 1–2 句话清晰界定适用边界（例如：“本工作主要评测了英文提示与特定分类模型，但定理 1 的数学保证独立于语言与规模”）。**不卑不亢，严禁写成道歉式的缺陷清单**。

---

### 2.8 Conclusion（结论：终局定论与精准未来展望）

Conclusion 是全文的终局裁决，控制在严格的**两段式结构（120–200 词）**，**绝非 Abstract 的机械复制**：

- **时态差异**：Abstract 是“预告片”，常用现在时（"We propose..."）；Conclusion 是“终局裁决”，核心发现必须使用**一般过去时或现在完成时**（"FedPE achieved...", "The Gate has closed the framing channel..."）。
- **两段式微观解剖**：
  - **第一段（重锚问题与因果机制闭环）**：从定论的最高视角重新锚定问题本质，用严密的因果逻辑交代方法为何能解决该痛点（"FedPE addresses dynamic drift by...; the memory mechanism retains..."），绝不罗列操作步骤。
  - **第二段（精准有深度的未来工作展望，避免假大空）**：
    - *反面典型*：`We hope our work will inspire future researchers to study this topic.`（极其空洞无力，暴露学生气）；
    - *正面典范（来自 FedPE）*：提出**具体明确且具有落地价值的技术延展方向**——例如：“未来的研究可以探索将同态加密（Homomorphic Encryption）机制整合进本架构，在保护模型传输隐私的同时，深入探究高强度隐私保护约束与通信计算开销之间的最优化权衡（Trade-off）”。
- **四大严苛禁忌**：严禁引入正文未出现过的新数据、严禁在此处书写局限性、严禁复制 Abstract 的原句、严禁出现 *"We hope..."* 等套话。

---

### 2.9 Ethics Considerations & Responsible Disclosure（伦理考量与披露）

- **独立章节**：伦理与负责任披露必须独立成节，严禁混在 Discussion 中。
- **披露（Responsible Disclosure）极简三要素**：
  1. *披露对象*：直接列出向哪些厂商或机构披露（使用机构全称）；
  2. *合规渠道*：指明走的是官方安全响应中心（SRC）渠道、漏洞披露策略指定渠道，还是直接联络；
  3. *角色称呼规范*：针对开源库或个人开发者，统一使用角色代称（如 *"the author of <repo-name>"*），**严禁直呼个人真实姓名**。
- **过滤琐碎细节**：不写具体沟通日期、往返邮件数量、承诺交付完整日志等琐事。厂商若已确认漏洞或发布补丁，补上一句官方确认即可。

---

### 2.10 论文信息架构速查表：细节该放哪里（Where Details Belong）

| 论文信息要素 | 唯一标准放置位置 | 归位理由与排版原则 |
| :--- | :--- | :--- |
| **核心 RQ、技术挑战、三大洞察、决定性指标** | Introduction 首尾、各实验段落首句 | 审稿人快速抓住贡献主线，信噪比最高 |
| **已有领域分支与技术分类学梳理** | Related Work 正文 | 构建技术演进漏斗与转折批判壁垒 |
| **物理环境、符号系统与通用优化方程** | Preliminaries 正文 | 纯净建模，严禁掺杂自研方法 |
| **设计决策的因果权衡与反事实理由** | Method / Defense 正文段落 | 论证技术合理性，回答“为何不选替代方案” |
| **具体超参、算力预算、采样温度、版本号** | §Setup（仅一句话概括）+ 附录全量表格 | 坚决不干扰方法本身的算法机制表述 |
| **基线补丁详情、Prompt 完整模板、系统提示词** | 附录 "Baselines and Defenses" | 供复现核查，绝不挤占正文黄金版面 |
| **人工审计规范、标注人员筛选流程、双盲检验** | 附录 "Human Audit"，正文仅留一个引用指针 | 保障严谨性同时避免打断评测节奏 |
| **统计检验方法（p-value）、单次运行声明、方差** | 表格 Caption 或 Table Notes（`\tiny`） | 审稿人查表时就近验证可信度 |
| **方法局限性（Limitations）** | Discussion 末尾独立段落（1–2 句话） | 客观界定技术边界，不卑不亢 |
| **未来具体技术延展（如加密/通信协同优化）** | Conclusion 第二段末尾 | 展现学术远见，杜绝空洞口号 |
| **伦理披露、合规声明、AI 工具使用说明** | 正文末尾独立 "Ethics Considerations" 节 | 满足顶会合规审计，不稀释学术论述 |

---

## 三、段落与句子级学术微雕规范（Sentence Crafting & Academic Diction）

### 3.1 明确主语与严谨修饰
- **彻底杜绝无主语动名词引导句**：确保动作发出者清晰无疑，避免审稿人回溯猜测。
  - *反例*：$\times$ *"Running the same detector on exact updates yields high accuracy."*（谁的检测器？与什么相同？）
  - *正例*：$\checkmark$ *"Running QEDFL's detection on exact updates yields high accuracy."*
- **比较连词 "instead of" 的精准挂载**：比较结构必须直接挂载在被替换的核心动作或实体上。
  - *反例*：$\times$ *"A rule that rejects a fixed fraction of uploads instead of the robust threshold..."*（句法脱节）
  - *正例*：$\checkmark$ *"Replacing the robust threshold of Phase 2a with a fixed rejection fraction..."*

### 3.2 极简原则与段落节律（Sentence Economy）
- **坚决删去车轱辘话**：前文已通过数据证实的结论，后文严禁再次泛泛复述（例如前面刚列出各攻击的具体准确率，后面紧接着又写 *"Neither attacker is markedly stronger than the other"*，应直接删去）。
- **句长控制与长短句节律**：超过 40 个单词的长句必须强制拆分。并列从句或宾语超过 3 个时，果断拆解为独立分句，形成轻重缓急的阅读节奏。
- **句中引用后移法则**：句中间大括号引用的 `(\cref{...})` 或 `\cite{...}` 尽量移至句末。严禁在主谓之间或紧密短语中插入长串引用打断阅读流。

### 3.3 语域正式度与术语全文统一
- **学术语域（Formal Register）动词替换**：严禁出现口语化动词及习语：
  - 用 `selects` / `identifies` 代替 `picks`
  - 用 `reduces` / `mitigates` 代替 `cuts`
  - 用 `performs worse` 代替 `fares worse`
- **维护全文统一的《术语基准表》**：建立术语白名单，全流程严守，避免混用引发歧义：
  - 统一写 *"authorized fact change"*，绝不混用 *"authorized update"*；
  - 统一写 *"correct decision"* 或 *"ground truth"*，绝不口语化写成 *"gold"*；
  - 严禁将未经攻击的基准决策 *"clean decision"* 随性称为 *"baseline"*。
- **大小写、字体与专有名词规范**：
  - 模型全名及其参数量属于整体专用名称，使用**正体**书写，规模直接连接（如 `kev-0.8B`, `Gemma4-12B`）；
  - 自研算法与系统名称采用**全大写或首字母大写正体**（如 LEVER / FedPE / QEDFL），正文中严禁使用打字机字体（`\texttt`）；
  - 冠词规范：正文中提及特指系统时必须带定冠词（*"the Provenance Gate"*）；但在论文标题、图表标题、表格第一列行名中，果断省略冠词以实现排版对齐（*"Our Defense: Provenance Gate"* 与 *"Our Attack: LEVER"* 并列）。

### 3.4 格式习惯与消除防御性限定
- **消除弥漫性的防御性套话**：论文的作用范围和威胁模型在引言和模型章节交代一次即可。绝不在后续每一个句子中机械追加 *"under our threat model / on the items they share / unless the verifier errs"* 等防御性套话，这只会暴露作者的信心不足。

---

## 四、图表视觉传达与双栏排版布局规范（Visuals & Typesetting）

### 4.1 图的视觉设计与 Caption 规范
- **贯穿全篇的 Running Example**：Figure 1 动机、Figure 2 架构与实验分析共享同一个真实实例。图中的具体数值必须出自真实实验日志，并在 LaTeX 源码注释中显式标注实验文件出处。
- **带编号的流程导引（Numbered Steps ①–⑥）**：架构图必须使用带圈数字 ①–⑥ 标注流程，编号置于边框上方避免遮挡文字；Caption 配合编号分步导读。
- **全篇统一的专业色系（Colorblind-safe Palette）**：全文统一配色——蓝色代表自身方案、橙色代表已有基线、红色代表对抗恶意样本；特定组件锁定固定专色。
- **Caption 语法与职责划分**：
  - 图标题采用 **IEEE Sentence case**（仅首字母大写）；表标题采用 **IEEE Title Case**（实词首字母均大写）；
  - 图标题必须阐明：测试数据集与模型架构（如 *"CIFAR-10 (CNN)"*）、统计口径（如 *"mean over three seeds"*）、攻击注入轮次与曲线虚实含义；
  - **核心准则**：Caption 的职责是阐明“图表展示了什么、该如何读懂它”；而“实验得出了什么震撼结论”必须留给正文。

### 4.2 表格自动化规范与指标呈现
- **坚决杜绝手工填表，脚本直写 TeX**：编写专用脚本直读底层实验数据输出 `.tex` 表格源码，确保实现逐字节一致的可复现性（Byte-level reproducibility）。
- **严格适配栏宽**：表头尽量短小，使用 `\cmidrule(lr){...}` 划分层级分组。
- **基线排列顺序全局固化**：所有表格中基线算法、模型的出现顺序必须自始至终绝对一致。自研方法所在行统一使用浅底色高亮（`\rowcolor`）。
- **指标标注宏与标准差规范**：
  - 最优数值使用统一宏标注（如 `\best{...}` 映射为粗体深红），并在表标题中显明标注规则；
  - 标准差统一格式化为 `{\tiny$\pm$}`；异常离散度在表注中明确标注解释（如：*"Std at most 4.9 except † (5.1–30.6)"*）；
  - 表格编号严格按正文首次引用顺序排列，源码中调整 `\begin{table}` 的先后位置以实现对齐。

### 4.3 双栏 LaTeX 浮动体三大硬性黄金法则
在顶会顶刊的双栏排版中，违反以下任意一条都会被审稿人直接打上“业余排版”标签：
1. **首次引用前置同页法则**：任何图表浮动体在页面阅读流向中，必须出现在**正文首次引用该图表之前**，且**必须与首次引用落在同一物理页面**（浮动体可在左栏上方，首次引用在右栏；跨栏通栏图表必须顶格置于当前页最上方）。
2. **版面饱和法则（No Bottom Void）**：除全文最后一页外，任何栏底绝对不允许出现超过 1.5 行以上的无故大片空白。
3. **跨栏浮动体下页生效机制**：跨栏浮动体（`figure*` / `table*`）在 LaTeX 编译原理中，最早只能渲染在**其源码定义位置的下一页**。因此，正文中对跨栏图表的首次引用句，必须精准落在那一页上。

### 4.4 浮动体四级调试阶梯与版面补偿技巧
当图表错位掉到后续页面时，**严禁暴力插入 `\vspace` 或硬编码断页符**。必须严格遵循以下四级调优阶梯：

```
+--------------------------------------------------------------------------+
|                      浮动体排版调试四级阶梯                              |
+--------------------------------------------------------------------------+
| 优先级 1: 移动源码中浮动体定义位置 (\begin{table})                      |
|           将 [!t] 浮动体在 TeX 源码中提前或延后半页，利用排版队列微调    |
|                                                                          |
| 优先级 2: 调整正文首次引用句的位置                                       |
|           将首次引用顺理成章地前移到节首总述句中                         |
|                                                                          |
| 优先级 3: 微调逻辑段落先后顺序                                           |
|           在保证语义流畅的前提下，微调段落顺序使引用落到目标页           |
|                                                                          |
| 优先级 4: 增补极具实质信息增量的长句                                     |
|           深度解释异常现象或机理，将段落自然顶过栏边界                   |
|                                                                          |
| 绝对禁忌: 严禁使用 \vspace 硬挤版面                                     |
+--------------------------------------------------------------------------+
```

- **破解“浮动体振荡（Oscillation）”现象**：
  - 出现振荡说明该段落恰好横跨在物理分页边界上。放弃在该段落内引用，**将首次引用点迁移至远离分页边界的绝对稳定区域**（例如放在该 Sub-section 的第一句总述句，或者移至段落末尾的定论句）。
- **消除段末孤行（Widows and Orphans Elimination）实现等长版面补偿**：
  - 仔细审查每一段的最后一行。如果最后一行仅仅孤零零挂着一两个单词，针对该段落进行微调微削，删减 2–3 个次要修饰词，使该孤行彻底缩回上一行。消除 3 个孤行就能硬生生省出整整 3 行正文高度，足以将落后的表格拉回本页！

---

## 五、参考文献规范与多源校验（Bibliography Verification）

### 5.1 多源核验与常见避坑清单
1. **多源自动化校验管道**：
   - 有 DOI 文献：调用 Crossref 官方 REST API（`api.crossref.org/works/<doi>`）自动化核对标准题录；
   - 无 DOI 顶会文献（NeurIPS/ICML/ICLR/USENIX）：经由 OpenAlex、DBLP、PMLR 官方页交叉验证。
2. **四大经典隐蔽 Bug 避坑清单**：
   - **作者姓与名颠倒**：将 `Kannan, Ramchandran` 误录为 `Ramchandran, Kannan`，导致正文缩写成了错误的 "R. Kannan"；
   - **纸质刊号年份 vs 网络首发年份脱节**：优先采用官方正式印刷出版年份；
   - **起止页码相差 1 页**：以官方收录的最终版 PDF 物理页码为唯一真值；
   - **会议集 Proceedings 命名年份与开会年份歧义**：严格遵循出版物正规标题中的版权年份，保持全文统一。

### 5.2 格式规范与战略引用
- **期刊与会议缩写全局一致**：严格遵循 IEEE 标准缩写规范（*IEEE Trans. Inf. Forensics Security*, *Proc. IEEE S&P* 等），绝不混用全称与缩写。
- **超长作者列表压缩**：在 `.bib` 头部配置 `IEEEtranBSTCTL` 控制文件，设置作者超标时自动折叠为 `"et al."` 压缩行数。
- **战略性文献引用**：在相关工作与对比中，有意识地检索并引用**目标期刊/目标会议近两年内发表的高质量相关成果**，精准迎合潜在审稿人圈层。

---

## 六、自适应领域微调与持续自进化系统（Adaptive Alignment & Self-Evolution）

为了让本写作与绘图规范具备跨学科自适应性与持续生命力，系统深度吸收了 **Orchestra-Research/AI-Research-SKILLs** 的双循环元架构设计：

### 6.1 领域与风格自适应对齐（Domain-Adaptive Alignment）
- **分类学路由（Taxonomy Routing）**：基于 `domain_taxonomies.json` 的关键词整词匹配打分（并报告置信度；无匹配或置信度低时需用 `--domain` 手动指定），将用户输入（Idea、实验数据或草稿）分类至安全隐私（S&P/CCS）、分布式系统（OSDI/SOSP）、机器学习（NeurIPS/ICML）、大模型与自然语言（ACL/EMNLP）等各大顶会赛道。
- **检索同主题标杆**：可选调用 arXiv API，取最近 2 年按相关度排序的同主题论文摘要（arXiv 不提供引用数，因此不是“高引/Spotlight”筛选）。
- **动态微调生成配置**：生成 `session_domain_profile.json`，自适应调整章节结构（如安全领域的 Threat Model、系统领域的 Hardware Testbed）与图表选型（如系统的 CDF 延迟图、网络流时延图）。

### 6.2 技能持续自进化与知识沉淀（Continuous Self-Evolution）
- **范文智能萃取（Pattern Distillation）**：通过 `self_evolve.py` 解析传入的优质顶会范文（如 MinerU 解析出的 Markdown 全文，先清洗 OCR 残留）或 arXiv 最新论文的摘要，用关键词模式匹配萃取候选顶会作者的高阶因果归因句式（Topic-Evidence-Mechanism）与经典转折批判句。
- **审核后写入（Review, then Apply）**：候选句默认只预览并与已有句式去重，人工审核后加 `--apply` 才追加进 `references/mechanism_sentence_bank.md`，同时在 `EVOLUTION_LOG.md` 记录来源与数量。

---

## 结语：顶级计算机论文的自检心法

一篇能够征服 CCF-A 顶会与顶级 Transactions 期刊审稿人的传世论文，其本质是一次**极高信噪比的严谨学术论辩**：

1. **在宏观上**：章节层层嵌套，引言的每一个挑战（C1–C3）与真实领域案例紧密绑定，直觉镜像回应，并在方法中精准建模，在实验 RQ 中严密验证；
2. **在相关工作上**：构建三层递进漏斗，以分类学梳理替代流水账，子节末尾以精准的转折批判句收口；
3. **在预备知识上**：恪守符号纯净性，为自研机制搭建清晰统一的数学舞台；
4. **在实验分析上**：坚决摒弃报菜名式的机械读表，重现象分析、轻数据堆砌、强归因映射，将实证结果紧密锚定在自研组件上；
5. **在工程与排版上**：图表脚本自动化直连数据，排版严格遵守首次引用同页原则，毫厘必争消除孤行。

严格遵循本规范，让每一篇付诸心血的研究，都能在审稿人面前展现出顶尖学者的专业素养与学术审美。
