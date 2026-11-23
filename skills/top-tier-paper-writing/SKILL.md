---
name: top-tier-paper-writing
description: "Write, revise and illustrate computer-science papers for top-tier venues (CCF-A conferences such as IEEE S&P, CCS, USENIX Security, OSDI, NeurIPS, ICML, ACL, and IEEE/ACM Transactions). Use when drafting or revising any paper section (title, abstract, introduction, related work, method, evaluation, discussion, conclusion), turning result tables into analysis prose, writing figure or table captions, making publication-quality plots or architecture diagrams, fixing float placement in two-column LaTeX, verifying references, or preparing arXiv and journal-extension submissions. 适用于计算机顶会/顶刊论文写作、润色、学术绘图、排版与投稿。"
compatibility: "Agent Skills format (Claude Code, OpenAI Codex, Google Antigravity app/CLI, and other compatible agents). Scripts need Python 3.8+ with matplotlib and numpy; layout checks need pdfLaTeX/XeLaTeX/LuaLaTeX with a 2020-10 or newer LaTeX kernel; arXiv lookups need network access and are optional."
metadata:
  version: "1.2.0"
  language: "zh-CN, en"
---

# Top-Tier Paper Writing & Academic Plotting Skill (顶会/顶刊论文全流程写作与学术绘图)

> 本 Skill 融合了计算机体系结构、安全、AI 与网络顶级会议（如 IEEE S&P）和权威顶刊（如 IEEE Transactions, compsoc 模板，Elsevier 顶刊如 FedPE）的实战写作规范，并深度整合了开源学术绘图前沿标准（Orchestra-Research `academic-plotting` 的双工作流体系与 Okabe-Ito 色盲友好调色板）。
>
> 核心目标：帮助 Agent 建立从**“绘图（架构图 + 实验图）”**到**“图表 Caption 规范”**再到**“正文深度机理归因写作”**的全闭环工程化能力。

## 使用约定（适用于任何 Agent）

- **路径**：本文中的 `scripts/…`、`references/…`、`templates/…` 都相对于**本 SKILL.md 所在目录**（下称 `<skill_dir>`）。运行脚本时使用完整路径，例如 `python3 <skill_dir>/scripts/check_layout.py main.aux`，输出文件写到用户的论文目录，而不是 `<skill_dir>`。
- **依赖**：绘图脚本需要 `python3 -m pip install -r <skill_dir>/requirements.txt`；排版检查需要 LaTeX；`domain_adapter.py` / `self_evolve.py` 的 arXiv 检索需要联网，离线时用 `--offline` 或改用本地文件。
- **按需加载**：本文件是总纲。只有进入对应步骤时才读取下表中的参考文件，不要一次性全部读入。
- **写入边界**：除 `self_evolve.py --apply`（且用户已审核候选句）外，不要修改 `<skill_dir>` 内的文件。

| 正在做的事 | 读取 |
| :--- | :--- |
| 起草或重写某一章节、逐段规划内容、句子与用语打磨、参考文献核验 | `references/section_anatomy_guide.md`（各章节宏观结构与段落解剖的完整版） |
| 写实验分析的“归因”句 | `references/mechanism_sentence_bank.md` |
| 绘图：尺寸、字号、配色 | `references/plotting_style_guide.md`；示例脚本见 `scripts/plot_*.py`、`scripts/gen_architecture_diagram.py` |
| 识别论文领域、补齐领域必备章节 | `scripts/domain_adapter.py` + `references/domain_taxonomies.json` |
| 安全/LLM 类会议稿的修改、排版与 arXiv 版本准备 | `references/case_lessons_ieee_sp.md`（IEEE S&P 实战案例） |
| 期刊稿、会议扩展投稿、参考文献逐条核对 | `references/case_lessons_ieee_tcc.md`（IEEE TCC 实战案例） |
| 把实验表格转成分析正文、设计架构图的提示词 | `templates/prompt_templates.md` |

---

## 一、核心工作流：从绘图到写作的端到端闭环（End-to-End Pipeline）

```
+----------------------------------------------------------------------------------------------------+
|                                Top-Tier Paper Pipeline 全流程闭环                                  |
+----------------------------------------------------------------------------------------------------+
| Phase 0: 领域自适应识别与微调对齐 (Adaptive Domain Profiling) [自适应模块]                          |
|   - 扫描论文 Idea/数据/关键词，自动识别所属计算机领域 (安全S&P / 系统OSDI / 机器学习NeurIPS / 网络 / NLP) |
|   - 可选检索 arXiv（近 2 年、按相关度排序；arXiv 无引用数据），获取目标领域同主题标杆文献            |
|   - 提取领域专属写作结构 (如安全 Threat Model, 系统 Testbed)、专用图表偏好与归因术语库，生成会话微调 Profile  |
|                                                                                                    |
| Phase 1: 架构与机制可视化 (Architecture & Diagrams)                                                |
|   - 抽取系统核心组件与交互时序                                                                     |
|   - 匹配架构布局：Pipeline 流水线式 / 分层式 (Layered) / 星型中心式 (Hub-and-Spoke)                 |
|   - 绘制现代简约学术风 (Modern Minimal) 架构图，标注数据流向与带圈步骤编号 ①–⑥                      |
|                                                                                                    |
| Phase 2: 实验数据可视化 (Data-Driven Visualizations)                                               |
|   - 数据维度匹配图表类型：多随机种子曲线 (带阴影方差) / 分组消融柱状图 / 跨架构方差对比图 / t-SNE 分布图  |
|   - 强制适配单/双栏排版尺寸 (3.4 in vs 6.9 in) 与 Okabe-Ito 色盲友好调色板                           |
|   - 纯脚本自动化生成矢量图 (.pdf) 与预览图 (.png)                                                  |
|                                                                                                    |
| Phase 3: 图表 Caption 规范化 (Caption Crafting)                                                    |
|   - 图采用 IEEE Sentence case，表采用 IEEE Title Case                                               |
|   - Caption 严守“只解释展示了什么与图例含义，绝不在 Caption 里抢先下研究结论”                      |
|                                                                                                    |
| Phase 4: 正文深度机理归因撰写 (Mechanism-Mapped Manuscript Drafting)                                |
|   - 实验段落恪守“总—分—归因”黄金模板：严禁机械读表报菜名                                            |
|   - 精选 1–2 个代表性极端指标/领先区间为佐证                                                        |
|   - 强行将实证现象映射回架构图中的自研机制 ①–⑥ 与数学算子                                          |
|                                                                                                    |
| Phase 5: 双栏 LaTeX 排版与版面精修 (Typesetting & Layout)                                          |
|   - 严守浮动体“首次引用同页前置”三大铁律                                                            |
|   - floatcheck 诊断编译 + check_layout.py 排查落后浮动体，四级调试阶梯调位，人工消除段末孤行      |
|                                                                                                    |
| Phase 6: 自主文献检索与 Skill 持续自进化 (Self-Evolution & Ingestion) [自进化模块]                 |
|   - 解析新文献 (MinerU Markdown 全文 / arXiv 最新论文摘要)                                          |
|   - 关键词模式匹配萃取候选因果归因句与批判性转折句，先预览、人工审核                                 |
|   - 审核后 --apply 追加进机制句式库，并记录进化日志 EVOLUTION_LOG.md                                |
|                                                                                                    |
| Phase 7: 修订、核验与投稿 (Revision & Submission)                                                  |
|   - 补实验后全文回溯旧表述；关键数字回到结果文件核对；参考文献多源逐条核验                         |
|   - 准备 arXiv 版本 / 期刊扩展投稿材料，见第十节与两份案例经验                                     |
+----------------------------------------------------------------------------------------------------+
```

---

## 二、绘图工作流 1：方法架构图与系统设计图（Workflow 1: System Diagrams）

架构图是整篇论文的视觉灵魂（通常作为 Figure 1 动机图或 Figure 2 系统全景图）。

### 1. 常见架构布局类型（Layout Topologies）
Agent 应根据方法论的本质拓扑结构选择最佳布局：
1. **流水线/阶段式（Sequential / Pipeline）**：从原始输入经过特征抽取、提示生成、中间变换到最终判决（从左至右，适合序列处理系统）。
2. **分层/堆叠式（Layered / Stacked）**：自底向上分为数据层、协议/通信层、核心计算层与应用判决层。
3. **中心辐射/联邦星型（Hub-and-Spoke / Centralized-Edge）**：中心协调服务端（Server）与周围分布式边缘节点（Clients）之间的上下行通信交互（如联邦学习、分布式系统）。
4. **双路径对比式（Dual-Path / Comparative）**：上方展示传统方案的失败路径，下方展示本文自研方案的旁路增强闭环。

### 2. 现代简约学术设计规范（Modern Minimal Academic Style）
- **框体规范**：使用浅色低饱和度填充背景（推荐柔和灰白、浅天蓝），边框使用深色细实线（0.8–1.2 pt），推荐适度微圆角（rounded corners），严禁浓重的 3D 渐变或炫目阴影。
- **带圈编号步骤（Numbered Badges ①–⑥）**：
  - 每一个关键数据流动步骤必须使用带圈数字编号 ①, ②, ③, ④, ⑤, ⑥；
  - 编号徽章置于框线外缘或箭头中段，**绝不遮挡模块文字**；
  - 正文写作时可以直接显式引用步骤编号（例如：*"As depicted in step ③ of Fig. 2, the features are concatenated..."*）。
- **统一专色锁定**：自研核心模块使用品牌专属强调色（如 Deep Navy `#0072B2` 或 Vibrant Teal `#009E73`），基线或对抗实体使用警示色（如 Vermilion `#D55E00`）。
- **格式输出**：必须直接导出为矢量的 PDF 格式（无损缩放）并保存生成源码（如 Python Matplotlib Patches / TikZ 脚本）。

---

## 三、绘图工作流 2：实验数据可视化规范（Workflow 2: Data-Driven Plots）

### 1. 图表类型匹配决策矩阵（Chart Selection Matrix）

| 实验目标与场景 | 最佳图表类型 | 核心视觉要素与实现规范 |
| :--- | :--- | :--- |
| **收敛速度与多轮精度** | 折线曲线图（Line Plot） | 多随机种子（至少 3 seeds）均值实线 + `fill_between` 阴影方差带 |
| **消融实验组件贡献** | 分组柱状图（Grouped Bar） | 垂直/水平柱状图 + 误差棒（Error Bar）+ 顶部精确增量百分比标注 |
| **高维表征聚类质量** | t-SNE / UMAP 散点图 | 明确的语义簇边界线（Convex Hull 或外接椭圆）+ 高对比度类标记 |
| **超参数敏感性与拐点** | 敏感性折线图（Sensitivity Plot） | 标注倒 U 型最高点（Optimal Trade-off Point），突出物理拐点 |
| **动态扰动抗压韧性** | 双阶段阶段对比图（Two-Phase Plot） | 中间加竖向虚线划分 Phase I 与 Phase II，展示扰动注入后的降幅 |
| **主干网络跨架构方差** | 箱线图/柱状跨度图（Box/Span Plot） | 横向对比各方法在换骨干网时的性能方差（突出自研方法的极小方差） |

### 2. 顶刊级 Matplotlib / Seaborn 工业配置规范
在编写绘图脚本时，必须严格注入以下全局样式配置：

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 字体与排版：适配 IEEE/ACM 双栏规范
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9,           # 正文基准字号
    "axes.titlesize": 10,     # 子图标题字号
    "axes.labelsize": 9,      # 坐标轴标签字号
    "xtick.labelsize": 8,     # 刻度数字字号
    "ytick.labelsize": 8,
    "legend.fontsize": 8,     # 图例字号
    "figure.titlesize": 11,
    "mathtext.fontset": "stix", # 让数学符号与 Times 字体完美融合
    "pdf.fonttype": 42,       # 保证文字作为文本嵌入 PDF 而非转曲点阵
    "ps.fonttype": 42,
})

# 2. 尺寸硬性标准
# IEEE/ACM 单栏宽度通常为 3.3–3.5 英寸；双栏通栏宽度为 6.8–7.0 英寸
FIG_WIDTH_SINGLE = 3.4
FIG_WIDTH_DOUBLE = 6.9
```

### 3. Okabe-Ito (Wong) 色盲友好调色板（强制集成）
全球约 8% 男性与 0.5% 女性患有不同程度的色觉障碍（CVD）。顶级会议与 IEEE Transactions 强烈要求图表在红绿色盲下依然具有高度可辨识度：

```python
# Okabe-Ito 经典 8 色十六进制定义
OKABE_ITO = {
    "black": "#000000",
    "orange": "#E69F00",        # 对比基线 1
    "sky_blue": "#56B4E9",      # 辅助模块
    "bluish_green": "#009E73",  # 自身强化组件
    "yellow": "#F0E442",
    "blue": "#0072B2",          # 自身主方法 (Primary Focus)
    "vermilion": "#D55E00",     # 恶意攻击/退化基线
    "reddish_purple": "#CC79A7" # 对比基线 2
}

# 设置绘图默认颜色循环
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=[
    OKABE_ITO["blue"],
    OKABE_ITO["orange"],
    OKABE_ITO["bluish_green"],
    OKABE_ITO["vermilion"],
    OKABE_ITO["reddish_purple"],
    OKABE_ITO["sky_blue"],
])
```

- **黑白打印友好原则**：除了色彩区分外，不同折线必须搭配不同的标记（Marker: `o`, `s`, `^`, `D`, `v`）与线型（Linestyle: `-`, `--`, `-.`, `:`），确保即使黑白复印打印也能清晰辨识。

---

## 四、Caption 撰写规范：语法、职责与禁忌

- **大小写规范**：
  - 图标题采用 **IEEE Sentence case**（仅首字母及专有名词大写，如 *"Fig. 3. Comparative analysis of accuracy across communication rounds for various baselines on Dirichlet non-IID scenario."*）；
  - 表标题采用 **IEEE Title Case**（实词首字母大写，如 *"Table 1. Performance (%) Comparison of Various Methods on Dirichlet Non-IID Scenario."*）。
- **职责边界划分**：
  - **Caption 的核心职责**：解释“图表展示了什么、坐标轴与图例的物理含义、以及测试的数据集与实验环境”；
  - **绝对禁忌**：严禁在 Caption 里抢先下研究结论（如写 *"which shows our method is much better"*）；所有分析与震撼结论**必须留给正文去引述**。

---

## 五、正文撰写：实验结果“重分析、轻堆砌、强归因”实战范式

### 1. 实验结果段落黄金法则：“总—分—归因”三步法

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

### 2. 四大高级分析实战范式

#### 范式 1：基线对比——抓难点与区间，重轨迹分析
- **低质写法（报菜名）**：在 CIFAR-10 上基线 A 为 65%，基线 B 为 89%，我们为 89.78%……在 CIFAR-100 上基线 A 为……
- **顶刊写法（FedPE 典范）**：大表中只挑最复杂的极限任务（如 CIFAR-100）列出 3 个核心数字（57.78%, 56.34%, 53.59%）和领先区间（2.35%–5.18%），其余基础任务用“各方法均在 95% 以上”一笔带过；分析收敛曲线时，不报轮数，而是分析**行为轨迹（Behavioral Trajectory）**：指出基线在分布漂移时发生断崖滑坡，而自研方案呈现平滑连续的学习轨迹，归因于跨轮约束机制。

#### 范式 2：参数敏感性——讲透倒 U 型拐点的物理本质
- **低质写法**：层数设为 1 时是 93%，设为 2 时是 97%，设为 4 时是 94%，所以 2 最好。
- **顶刊写法（FedPE 典范）**：
  - 现象：性能呈现**先上升后下降**的倒 U 型；
  - 前期上升归因：层数适度增加带来了深层特征抽象能力的渐进增强（*progressive enhancement of deep feature abstraction*）；
  - 后期下降归因：参数激增引发过拟合，模型开始**“死记硬背训练样本中的噪声而非学习底层泛化规律”**（*memorize noise rather than learning underlying patterns*）；
  - 结论：因此该取值是表达力与防过拟合之间的最佳工程平衡点。

#### 范式 3：模型结构鲁棒性——比方差与解耦能力
- **低质写法**：我们在 ResNet 上为 55%，在 EfficientNet 上为 54%，都高于基线。
- **顶刊写法（FedPE 典范）**：
  - 抓核心指标：**跨主干网性能方差（Variance Across Backbones）**。自研方法方差仅为 0.88%（*negligible variance*），而基线暴跌 6.87%；
  - 升华机理：证明方法**“成功将分布自适应能力与特定骨干网络的特征提取过程进行了解耦”**（*decouples distribution adaptation from backbone-specific feature learning*）；
  - 归因：自研提示模块天然与底层架构无关（Architecture-agnostic），而历史约束抑制了跨轮梯度冲突。

#### 范式 4：两阶段动态抗压测试——评估扰动下的衰减韧性
- **实验设计**：Phase I（稳定基线期，Rounds 1–100） $\to$ Phase II（动态扰动期，Rounds 101–200，随机屏蔽 20% 数据）。
- **分析重点**：对比**从 Phase I 到 Phase II 的性能衰减幅度（Drop Rate）**——自研方法仅衰减 0.47%，而基线剧烈滑坡 1.34%–4.19%，以此实证系统的高弹性（Resilience）。

---

## 六、全生命周期章节写作规范与微观段落解剖

除了实验章节外，全篇各章节必须严格执行以下段落展开规范：

### 1. Title & Abstract
- **Title**：`[系统名]: [核心机制/解决的问题] in/for [应用领域]`；
- **Abstract 5 句骨架**：
  - 句 1：高价值背景与宏观重要性；
  - 句 2：常规方案与一般痛点；
  - 句 3：已有 SOTA 的成就与**两个残留核心技术挑战**；
  - 句 4：本文系统名与**对称的两大核心组件解法**；
  - 句 5：最具代表性的决定性指标区间与实用价值。

### 2. Introduction（7 步递进叙事流）
- **第 1 段（场景与 Running Example）**：快速切入场景，段末直接引入 Figure 1 贯穿实例；
- **第 2 段（SOTA 缺陷与量化实证）**：指出前沿方案本质盲区，并给出压倒性定量实证；
- **第 3 段（双挑战与现实案例映射）**：提出 Challenge 1 与 Challenge 2，**每个挑战必须直接绑定一个真实领域案例**（如医疗转诊动态漂移、图像分类历史遗忘）；
- **第 4 段（镜像直觉响应段）**：以 *"Intuitively, we propose..."* 引导，与第 3 段呈 1-to-1 镜像对齐，阐述双直觉解法；
- **第 5 段（系统名与挑战映射）**：正式介绍自研系统，模块句中显式打上 `(C1)`、`(C2)` 映射标签；
- **第 6 段（防御扩展/理论保证）**：用 *"We further propose..."* 独立引出扩展贡献；
- **第 7 段（4 条精炼贡献列表）**：(1) 现象与问题发现；(2) 核心算法；(3) 理论保障机制；(4) 决定性评测结果。

### 3. Related Work（三层递进漏斗）
- **组织结构**：§2.1 目标宏观领域 $\to$ §2.2 核心支撑技术 $\to$ §2.3 交叉前沿领域；
- **分类学梳理**：按技术路线分类归纳，严禁按作者年份流水账陈列；
- **子节末黄金转折批判句**：每个子节末尾必须用独立段落指出已有方案的共同死穴。

### 4. Preliminaries & Problem Formulation（符号纯净性）
- **绝对解耦**：严禁在此处引入自研方法名与自研模块；
- **标准三元组建模**：严谨定义参与方环境符号 $\to$ 传统全局优化方程 $\to$ 前沿联合优化方程，为自研机制埋下伏笔。

### 5. Methodology（三层解构范式）
- **§4.1 总览**：Figure 1 全流程框架图 + Algorithm 1 伪代码（行号严格映射后续公式）；
- **技术子模块三层展开**：
  - *Layer 1: 通俗直觉目标（Intuitive Goal）*：用大白话讲清模块想干嘛；
  - *Layer 2: 规范前向建模（Formal Formulation）*：公式符号规整，定义输入输出与算子；
  - *Layer 3: 优化与梯度流机理（Working Mechanism）*：拆解前向计算与梯度更新策略。
- **自适应因子物理设计**：如 $\lambda(1 - p(w))$，解释当瞬时精度低时强制保护历史、精度高时释放探索自由度的动态平衡物理直觉。
- **超参隔离**：具体数值（学习率、轮数）移入 Setup 和附录，正文只讲参数控制作用。

### 6. Discussion（回答 Why，绝不重复 What）
- 5 个结构化段落：(1) 深层机理本质；(2) 可迁移设计原则；(3) 放松威胁模型与自适应攻防；(4) 更广泛的生态影响；(5) 1–2 句客观冷静的局限性界定（不道歉）。

### 7. Conclusion（终局定论视角）
- **两段式严格控制（120–200 词）**：
  - 第一段：时态切换为一般过去时/现在完成时，因果逻辑闭环收束；
  - 第二段：提出具体明确、具有深度落地价值的技术延展方向（如结合同态加密、权衡隐私与通信开销），坚决杜绝 *"We hope..."* 等空洞口号。

---

## 七、双栏 LaTeX 排版三大铁律与四级调试阶梯

1. **三大硬性黄金法则**：
   - *首次引用前置同页法则*：阅读流向中浮动体必须在首次引用之前或同页，跨栏图顶格置于页顶；
   - *版面饱和法则*：除末页外，栏底绝对不允许出现超过 1.5 行以上的无故大片空白；
   - *跨栏浮动体下页生效机制*：`figure*` 最早只能渲染在源码定义处的下一页，正文首次引用必须安排在那一页上。
2. **四级调试阶梯（严禁使用 `\vspace`）**：
   - 优先级 1: 移动源码中 `\begin{figure/table}` 定义位置提前半页；
   - 优先级 2: 调整正文首次引用句移至节首总述句；
   - 优先级 3: 微调逻辑段落先后顺序；
   - 优先级 4: 增补极具实质信息增量的解释长句；
   - **消除段末孤行（Widows/Orphans）**：微调删减段末仅剩 1–2 个单词的行尾，消除 3 个孤行可拉回 3 行正文高度，化解浮动体跨页与振荡。

3. **浮动体检查的具体用法**：

```bash
cp scripts/floatcheck.sty /path/to/paper/      # 放到 main.tex 旁边
cd /path/to/paper
# 诊断编译（无需修改源码；运行两次让位置稳定）
pdflatex -jobname=main "\RequirePackage{floatcheck}\input{main}"
pdflatex -jobname=main "\RequirePackage{floatcheck}\input{main}"
python3 /path/to/skill/scripts/check_layout.py main.aux
```

- 输出中 `FAIL` 为违反铁律（浮动体落后于首次引用页、`figure*` 定义太晚），`WARN` 为同页但阅读顺序靠后、从未被引用等；
- 每次修改正文前后各跑一次并对比，**任何改动都不能让 FAIL 变多**；
- 也可以把 `\usepackage{floatcheck}` 作为最后一个宏包加入导言区；该宏包只写入 whatsit，不改变版面。

---

## 八、配套工具脚本使用说明（Scripts & References）

本 Skill 目录下附带了一整套可直接执行的生产级绘图、排版与智能进化工具：

- `scripts/domain_adapter.py`：领域识别与配置生成（按 `domain_taxonomies.json` 关键词整词匹配打分并给出置信度，无匹配时要求 `--domain` 指定；可选检索近 2 年 arXiv 同主题论文，`--offline` 跳过；生成 `session_domain_profile.json`）；
- `scripts/self_evolve.py`：句式萃取工具（解析本地 MinerU Markdown 全文或 arXiv 摘要，清洗 `<sub>` 等 OCR 残留、按句切分并用关键词模式筛出候选因果/转折/图表句式，与句式库去重；默认仅预览，人工审核后加 `--apply` 才写入句式库与 `EVOLUTION_LOG.md`）；
- `scripts/plot_data_curves.py`：标准多种子收敛曲线绘制脚本（自动注入 Okabe-Ito 配色、`fill_between` 阴影方差、IEEE 单栏尺寸 3.4 in、自动导出矢量 PDF）；
- `scripts/plot_bar_ablation.py`：分组消融柱状图脚本（包含误差棒、顶部数值标签与紧凑布局）；
- `scripts/gen_architecture_diagram.py`：矢量系统架构图生成脚本（使用 Matplotlib Patches 自动绘制带圈序号 ①–⑥、双向通信通道与模块边界）；
- `scripts/floatcheck.sty` + `scripts/check_layout.py`：浮动体位置检查。`floatcheck.sty` 在诊断编译中用 `\pdfsavepos` 记录每个浮动体与每处 `\ref`/`\cref`/`\autoref` 的页码和坐标，`check_layout.py` 据此检查三大铁律（同页且在阅读顺序上先于首次引用；`figure*` 最早在定义处下一页；从日志中的 `Underfull \vbox ... while \output is active` 推断栏底空白），并汇总浮动体相关警告；有错误时退出码为 1。段末孤行无法从日志检测，需人工查看 PDF；
- `references/domain_taxonomies.json`：计算机各顶级领域（安全、系统、机器学习、NLP）结构要求与图表偏好分类库；
- `references/plotting_style_guide.md`：详细的 IEEE/ACM 图表尺寸、字号层级规范与完整配色代码；
- `references/mechanism_sentence_bank.md`：顶会顶刊经典因果归因学术句式库（支持自进化热追加）；
- `references/section_anatomy_guide.md`：全生命周期章节与段落解剖的完整版（本文第六节为其摘要），另含句子微雕、表格规范与参考文献核验；
- `references/case_lessons_ieee_sp.md` / `references/case_lessons_ieee_tcc.md`：两篇真实论文（IEEE S&P 会议稿、IEEE TCC 期刊稿）修改与投稿中沉淀的具体经验与正反例；
- `templates/prompt_templates.md`：“实验表格 → 归因正文”与“架构图设计”提示词模板；
- `requirements.txt`：脚本的 Python 依赖。

---

## 九、自适应调整与自进化模块运行机制（Adaptive & Self-Evolution Modules）

借鉴 **Orchestra-Research/AI-Research-SKILLs** 的元编排（Meta-Orchestration）与双循环架构（Inner-loop 高效生产，Outer-loop 反思进化），本模块赋予 Agent 持续感知与自我迭代的能力：

### 1. 领域自适应对齐模块（Domain-Adaptive Profiler）
在面对任何新的论文写作需求时，Agent 在执行正文编写前自动执行 Phase 0：
1. **领域与目标顶会路由（Domain Routing）**：
   - 运行 `python3 scripts/domain_adapter.py --file idea.md`，按关键词整词匹配打分，映射至 `references/domain_taxonomies.json` 分类树（如 `security_privacy` 对标 S&P/CCS；`distributed_systems` 对标 OSDI/SOSP；`machine_learning_fl` 对标 NeurIPS/TCC）；
2. **标杆文献动态检索（Exemplar Retrieval）**：
   - 查询 arXiv API，取最近 2 年按相关度排序的同主题论文摘要（arXiv 不提供引用数，因此不是“高引”筛选；离线或网络受限时用 `--offline`）；
   - 检查输出中的 `selection.confidence`：为 `low`/`none` 时，Agent 应向用户确认领域并用 `--domain` 指定，不要猜测；
3. **微调配置文件生成（Profile Generation）**：
   - 动态输出 `session_domain_profile.json`，在会话中覆盖如下规则：
     - **结构约束**：如安全领域强制插入 `Threat Model and Assumptions`，系统领域强制插入 `Testbed & Workload Specs`；
     - **图表矩阵微调**：如系统领域优先调度 CDF 延迟图与耗时 Breakdown 堆叠图，安全领域优先调度攻击预算-防御效用曲线；
     - **词汇调优**：激活特定领域的学术因果动词（如解耦、抑制、正交投影、梯度扰动上界）。

### 2. 文献检索与 Skill 持续自进化模块（Self-Evolution Engine）
让句式库随着用户提供的优秀范文持续扩充（基于关键词模式匹配，所有候选都需人工审核）：
1. **多源输入摄入（Multi-Source Ingestion）**：
   - 支持解析用户提供的 MinerU Markdown（如 FedPE 等顶刊全文，效果最好）或指定 arXiv 查询词拉取最新论文的**标题与摘要**（arXiv API 不返回全文）；
   - 输入先经清洗：去除 `<sub>`/`<sup>` 等 OCR 标签、图片、公式与 `[12]` 类引用标号，再按句切分；
2. **高阶表达模式萃取（Pattern Distillation）**：
   - 对每个句子用关键词模式识别出（含残留乱码、碎片单词的句子会被丢弃）：
     - *因果归因句型（Causal Attributions）*：寻找包含 `stems from`, `attributable to`, `decouples ... from`, `penalizes ... thereby preventing` 等深层机制句；
     - *顶会转折批判句型（Rhetorical Transitions）*：寻找指出已有工作本质死穴的批判性句型；
     - *图表论述句型（Figure Phrasings）*：提炼顶会作者如何将实验折线与消融柱状图无缝串联至正文逻辑中；
3. **审核后写入（Review, then Apply）**：
   - 默认只预览候选句（与句式库已有句子自动去重）；Agent 应把候选展示给用户，确认后再加 `--apply` 写入 `references/mechanism_sentence_bank.md`；
   - 写入时同时在 `EVOLUTION_LOG.md` 中记录时间、来源与新增数量。

---

## 十、修订、参考文献核验与投稿（Phase 7: Revision & Submission）

1. **补实验后的全局回溯**：每加一组实验，通读引言、贡献列表、威胁模型、理论适用范围、实验设置、结论与摘要中的数字，修改被新结果推翻或削弱的句子（案例见 `references/case_lessons_ieee_tcc.md` §1.1）。
2. **数据与运行实例核对**：正文中的关键数字和贯穿实例逐一回到实验结果文件核实，数据不支持的说法一律不写（见 `references/case_lessons_ieee_sp.md` 第一节）。
3. **参考文献逐条核验**：对每条文献在出版方页面、DBLP 或 arXiv 中至少两个来源核对作者、标题、年份、会议/期刊与页码，常见错误类型与格式规范见 `references/section_anatomy_guide.md` 第五节和 `references/case_lessons_ieee_tcc.md` 第 5 节。
4. **改动后的版面回归**：每次改正文前后各跑一次 floatcheck 诊断编译与 `check_layout.py` 并对比，`FAIL` 不得增加；同时核对页数上限。
5. **arXiv 版本**：`\pdfoutput=1`、删除源码注释但保留行末 `%`、附带与 `.bib` 一致的 `.bbl`、在空目录中独立编译验证（见 `references/case_lessons_ieee_sp.md` 第七节）。
6. **会议论文扩展为期刊稿**：投稿材料清单与“新增内容占比”说明的写法见 `references/case_lessons_ieee_tcc.md` 第 6 节。
