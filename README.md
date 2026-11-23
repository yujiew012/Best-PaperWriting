# 通用计算机顶会/顶刊论文写作规范与学术绘图 Agent Skill (Best-PaperWriting)

[![Skill: top-tier-paper-writing](https://img.shields.io/badge/Agent%20Skill-top--tier--paper--writing-blueviolet.svg)](.agent/skills/top-tier-paper-writing/SKILL.md)
[![Domain: Computer Science](https://img.shields.io/badge/Domain-Computer%20Science%20(AI%20%7C%20Security%20%7C%20Systems)-blue.svg)]()
[![Target: Top-tier Conf & Trans](https://img.shields.io/badge/Target-CCF--A%20%2F%20IEEE%20Trans%20%2F%20ACM-brightgreen.svg)]()
[![Aesthetics: Okabe-Ito & Modern Minimal](https://img.shields.io/badge/Aesthetics-Okabe--Ito%20%7C%20Modern%20Minimal-orange.svg)]()

> 本项目已正式封装为生产级 **Antigravity / Coding Agent Skill (`top-tier-paper-writing`)**！
>
> 综合提炼自计算机顶级安全/AI会议（如 IEEE S&P）及权威期刊（如 IEEE Transactions, compsoc 模板，Elsevier 权威网络期刊，如 FedPE 实战案例），并深度结合开源顶尖学术绘图标准（**Orchestra-Research `AI-Research-SKILLs` 中的 `academic-plotting` 双工作流体系**）。
> 
> 旨在从**“发表过多篇顶会/顶刊的资深博士生与审稿人”**视角，打造一套**从绘图到语言表述完全贯通的一体化闭环工具包**：
> 1. **绘图工作流 1（架构图）**：现代简约学术风（Modern Minimal），规范标注数据流向与带圈步骤编号 ①–⑥；
> 2. **绘图工作流 2（实验图）**：集成 Okabe-Ito 色盲友好调色板、单双栏尺寸适配（3.4 in vs 6.9 in）与误差阴影曲线；
> 3. **图表 Caption 规范**：严格区分 IEEE Sentence Case 与 Title Case，杜绝在 Caption 中下主观结论；
> 4. **全生命周期正文微观写作**：引言“双挑战—双案例—双直觉”对称推进，实验段落“总—分—归因”彻底终结“报菜名堆数据”；
> 5. **双栏排版精修**：浮动体同页前置三大铁律与消除孤行（Widows/Orphans）版面补偿。

---

## 一、Skill 架构与工程目录结构

本项目包含完整开箱即用的 Agent Skill 结构，位于 `.agent/skills/top-tier-paper-writing/` 与 `skills/top-tier-paper-writing/`：

```
.agent/skills/top-tier-paper-writing/
├── SKILL.md                          # Skill 核心指导手册（Agent 提示词与规范总览）
├── EVOLUTION_LOG.md                  # Skill 自进化历史与知识沉淀日志 [新]
├── scripts/                          # 工业级学术绘图、排版与智能进化自动化脚本
│   ├── domain_adapter.py             # 领域自适应对齐引擎 (自动识别领域、检索 arXiv 标杆并微调) [新]
│   ├── self_evolve.py                # 技能自进化引擎 (解析新文献、萃取高阶因果句式并热更新) [新]
│   ├── gen_architecture_diagram.py  # 架构图生成脚本 (Modern Minimal + 带圈编号 ①–⑥ + 矢量 PDF)
│   ├── plot_data_curves.py           # 收敛曲线绘制脚本 (Okabe-Ito 色盲安全 + 阴影方差 + IEEE 单栏)
│   ├── plot_bar_ablation.py          # 消融实验分组柱状图脚本 (误差棒 + 精准百分比标注)
│   └── check_layout.py               # 双栏排版浮动体错位与版面空洞自动检查工具
├── references/                       # 视觉规范、分类库与学术句式参考基准
│   ├── domain_taxonomies.json        # 计算机各大顶级领域 (安全/系统/ML/NLP) 结构要求与图表偏好 [新]
│   ├── plotting_style_guide.md       # IEEE/ACM 物理尺寸、字号层级、色板十六进制速查
│   └── mechanism_sentence_bank.md    # 顶会顶刊“现象 -> 归因 -> 机制映射”经典学术句式库 (支持自进化热追加)
└── templates/                        # 交互与转换模板
    └── prompt_templates.md           # “实验表格 -> 深度归因正文” 与 “架构图设计” Prompt 模板
```

---

## 二、端到端闭环：从绘图到语言表述的全流程（Pipeline）

```
+----------------------------------------------------------------------------------------------------+
|                                Top-Tier Paper Pipeline 全流程闭环                                  |
+----------------------------------------------------------------------------------------------------+
| Phase 0: 领域自适应识别与微调对齐 (Adaptive Domain Profiling) [自适应模块]                          |
|   - 扫描论文 Idea/数据/关键词，自动识别所属计算机领域 (安全S&P / 系统OSDI / 机器学习NeurIPS / 网络 / NLP) |
|   - 自动联网检索 arXiv / 顶会数据库，获取目标领域近 1-2 年高水平标杆文献                             |
|   - 提取领域专属写作结构 (如安全 Threat Model, 系统 Testbed)、专用图表偏好与归因术语库，生成会话微调 Profile  |
|                                                                                                    |
| Phase 1: 架构与机制可视化 (Architecture & Diagrams)                                                |
|   - 对应 Workflow 1：根据方法拓扑选择 Pipeline / 分层 / 星型中心布局                                |
|   - 绘制现代简约学术风 (Modern Minimal) 架构图，标注数据流向与带圈步骤编号 ①–⑥                      |
|                                                                                                    |
| Phase 2: 实验数据可视化 (Data-Driven Visualizations)                                               |
|   - 对应 Workflow 2：折线收敛曲线 (带阴影方差) / 分组消融柱状图 / 跨架构方差对比图 / t-SNE 分布图      |
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
|   - 运行检查脚本排查落后浮动体，四级调试阶梯调位，消除段末孤行实现等长空间补偿                     |
|                                                                                                    |
| Phase 6: 自主文献检索与 Skill 持续自进化 (Self-Evolution & Ingestion) [自进化模块]                 |
|   - 自动扫描解析新文献 (MinerU Markdown / arXiv 最新录用论文)                                       |
|   - 自动萃取高阶因果机理归因表达 (Causal Patterns) 与顶会批判性转折句                                |
|   - 热补丁 (Hot-patch) 沉淀进机制句式库，记录进化日志 EVOLUTION_LOG.md，实现技能库“越用越强”       |
+----------------------------------------------------------------------------------------------------+
```

---

## 三、绘图工作流 1：方法架构图与系统设计图（Workflow 1: System Diagrams）

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

## 四、绘图工作流 2：实验数据可视化规范（Workflow 2: Data-Driven Plots）

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
FIG_WIDTH_SINGLE = 3.4   # 单栏
FIG_WIDTH_DOUBLE = 6.9   # 双栏通栏
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
```

- **黑白打印友好原则**：除了色彩区分外，不同折线必须搭配不同的标记（Marker: `o`, `s`, `^`, `D`, `v`）与线型（Linestyle: `-`, `--`, `-.`, `:`），确保即使黑白复印打印也能清晰辨识。

---

## 五、Caption 撰写规范：语法、职责与禁忌

- **大小写规范**：
  - 图标题采用 **IEEE Sentence case**（仅首字母及专有名词大写，如 *"Fig. 3. Comparative analysis of accuracy across communication rounds for various baselines on Dirichlet non-IID scenario."*）；
  - 表标题采用 **IEEE Title Case**（实词首字母大写，如 *"Table 1. Performance (%) Comparison of Various Methods on Dirichlet Non-IID Scenario."*）。
- **职责边界划分**：
  - **Caption 的核心职责**：解释“图表展示了什么、坐标轴与图例的物理含义、以及测试的数据集与实验环境”；
  - **绝对禁忌**：严禁在 Caption 里抢先下研究结论（如写 *"which shows our method is much better"*）；所有分析与震撼结论**必须留给正文去引述**。

---

## 六、正文撰写：实验结果“重分析、轻堆砌、强归因”实战范式

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
1. **基线对比**：抓最难任务与领先区间，收敛曲线重在分析**行为轨迹（Behavioral Trajectory）**；
2. **参数敏感性**：剖析倒 U 型拐点的**物理权衡本质（前期特征抽象增强 vs 后期过拟合噪声记忆）**；
3. **模型结构鲁棒性**：对比**跨骨干网方差（Variance Across Backbones）**，升华出“分布自适应与主干网解耦”；
4. **两阶段动态抗压测试**：Phase I 稳定期 $\to$ Phase II 扰动期，对比**衰减幅度（Drop Rate）**论证高韧性。

---

## 七、全生命周期章节写作规范与微观段落解剖

### 1. Title & Abstract
- **Title**：`[系统名]: [核心机制/解决的问题] in/for [应用领域]`；
- **Abstract 5 句骨架**：背景 $\to$ 常规痛点 $\to$ SOTA 成就与**双核心挑战** $\to$ 本文方案与**双组件对称响应** $\to$ 决定性指标区间。

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

## 八、双栏 LaTeX 排版三大铁律与四级调试阶梯

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

---

## 九、自适应调整模块与自进化模块（Adaptive & Self-Evolution Modules）

借鉴 **Orchestra-Research/AI-Research-SKILLs** 的元编排（Meta-Orchestration）与双循环架构，系统提供两大前沿自动化子系统：

### 1. 自适应领域识别与微调模块（Adaptive Domain Alignment）
根据用户的具体论文方向，自动定制结构、图表与机理归因要求：
- **运行命令**：
  ```bash
  python3 .agent/skills/top-tier-paper-writing/scripts/domain_adapter.py --file idea.md --output session_domain_profile.json
  # 或直接传文本/关键词
  python3 .agent/skills/top-tier-paper-writing/scripts/domain_adapter.py --text "Zero-knowledge verifiable defense against backdoor poisoning in edge FL"
  ```
- **自动化工作逻辑**：
  1. **领域与赛道识别**：自动匹配所属领域（安全隐私 `security_privacy`、分布式系统 `distributed_systems`、机器学习/联邦 `machine_learning_fl`、大语言模型 `nlp_llm`）；
  2. **顶会标杆检索**：自动调用 arXiv API 检索该领域最近 1–2 年的高引/Spotlight 论文，解析其结构范式；
  3. **动态规则注入**：生成 `session_domain_profile.json`，在写作时自动补齐该领域强制章节（如安全必备的 *Threat Model*，系统必备的 *Hardware Testbed & Tail Latency*）与最优图表组合（如系统 CDF 图、安全攻击预算折线图）。

### 2. 文献检索与 Skill 持续自进化模块（Skill Self-Evolution）
让 Skill 能够像优秀研究者一样终身自主学习前沿顶会的写作与绘图精华：
- **运行命令**：
  ```bash
  # 方式 A：解析本地优质顶会论文 (如 MinerU 解析出的 Markdown)
  python3 .agent/skills/top-tier-paper-writing/scripts/self_evolve.py --file /path/to/mineru_paper.md

  # 方式 B：指定前沿主题自动在线检索 arXiv 录用论文自进化
  python3 .agent/skills/top-tier-paper-writing/scripts/self_evolve.py --arxiv_query "adversarial differential privacy" --max_papers 3
  ```
- **自动化进化逻辑**：
  1. **模式萃取**：智能扫描论文全文，精准萃取因果机理归因句（Causal Attributions）、文献综述批判转折句（Rhetorical Transitions）以及图表表述手法；
  2. **知识库热更新**：自动将提炼的高阶句式沉淀追加到 `references/mechanism_sentence_bank.md`；
  3. **进化足迹留痕**：在 `EVOLUTION_LOG.md` 中记录时间戳、输入来源与新增能力，实现技能库**“越用越强、自我进化”**。
