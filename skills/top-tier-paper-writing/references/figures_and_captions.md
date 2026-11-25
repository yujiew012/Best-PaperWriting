# Figures, Tables & Captions（图、表与 Caption）

> 适用：绘制架构图或实验图、设计表格、撰写/审查 Caption。
> 绘图一律通过 `scripts/` 中的脚本完成（样式由 `scripts/pubstyle.py` 统一注入），**不要**手写 rcParams 或手算统计量。

---

## 0. 先做图表计划（Figure plan），再画图

画任何图之前，先从 claim map（`writing/claims_and_evidence.md`）生成图表计划 `figure_plan.json`（格式见 `assets/figure_plan_example.json`），并校验：

```bash
uv run <skill_dir>/scripts/figure_plan.py figure_plan.json --claims claim_map.json --tex paper/main.tex --md figure_plan.md
```

- **一图一论点**：每一行（图或表）只承载 claim map 中的一个 claim，先写好 Caption 的要点句（`caption_takeaway`）再动手画；承载不了任何 claim 的图移到附录。每个 gap / result / advantage 类 claim 都必须有图或表。
- **状态**：`draw` 只用于用户已说明机制的示意图（架构图、流程、威胁模型）；凡是展示结果的图（曲线、渲染、示例输出、数值）在用户提供数据前一律是 `placeholder`，**NEVER** 编造结果图、曲线或数值。占位图用 `assets/figure_placeholders.tex` 的 `\FigPlaceholder{宽}{高}`，并把计划写进 Caption：`\caption{\FigPlan{claim C4; 需要 ...}...}`；`figure_plan.py --tex` 会列出所有残留占位，投稿前必须清零。
- **`material`**：写清楚缺什么（哪些场景、哪些基线、哪个指标与坐标轴）。计划表进入作者报告（`make_report.py`）。
- **Figure 1 按路线选**（`writing/routing.md` §3）：`failure` → 基线失败、本文修复的诊断图；`cost` → 旧机制与本文机制对照并标出代价；`capability-gap` → 真实输入到输出的展示图；L3/L4 → 标注规律或反转的曲线；L7 → 资源本身与规模；L8 → 被测现象。`figure_plan.py` 会提示不匹配。
- **Caption 风格随会议**（`venues.json` 的 `caption_content`）：`neutral`（IEEE、ACM、USENIX、ACL、LNCS）——Caption 只描述、不下结论（W203）；`takeaway`（NeurIPS、ICML、ICLR）——首句是 3–12 词的要点句（如 *"Lower resolution, weaker refusals."*），随后说明各面板与读法（W204 检查首句长度）。

---

## 1. 硬性规则

1. **MUST** 使用真实实验数据作图；图中每个数字都能追溯到结果文件（在 LaTeX 源码注释中写明出处）。**NEVER** 用示例数据（`assets/*_example.*`、`--demo`）生成论文插图。
2. **MUST** 按目标会议的版式定宽（见 §3.3）：绘图脚本与 `check_figure.py` 都传 `--venue <venue>`；不传时按 IEEE（单栏 3.4 in、跨栏 6.9 in）。导出矢量 PDF（字体为 TrueType/Type 42 嵌入，无 Type 3）。**NEVER** 先按 IEEE 宽度出图再在 LaTeX 里缩放：字号会随之变小。
3. **MUST** 使用 Okabe-Ito 色盲友好调色板，并全篇固定语义：蓝 `#0072B2` = 本文方法，橙 `#E69F00` / 紫 `#CC79A7` = 基线，绿 `#009E73` = 变体/支撑组件，朱红 `#D55E00` = 攻击/退化/对抗实体。朱红只通过 `--adverse` 显式指定，脚本不会按顺序把它分给普通系列；有朱红系列时其余系列自动避开橙色。
4. **MUST** 黑白可辨：不同曲线同时使用不同标记（`o s ^ D v`）与线型（`- -- -. :`），脚本已自动分配。
5. **MUST** 多随机种子（≥ 3 seeds）报告均值 ± 标准差；曲线用阴影带，柱状图用误差棒。误差棒/阴影只表示真实的不确定性（多次运行的差异，或对测试样本的置信区间）；只有单次运行时脚本会省略它们（**NEVER** 画零宽误差棒），此时必须在 Caption 中说明运行次数。
6. **NEVER** 在 Caption 中下结论（见 §5）。

---

## 2. 架构图（Figure 1 / Figure 2）

### 2.1 选择布局

| 方法本质 | 布局 | 示例 |
| :--- | :--- | :--- |
| 输入经多个阶段变换到输出 | **Pipeline**（从左到右） | 特征抽取 → 提示生成 → 判决 |
| 自底向上的层级 | **Layered**（从下到上） | 数据层 → 协议层 → 计算层 → 应用层 |
| 中心协调 + 分布式节点 | **Hub-and-Spoke** | 联邦学习服务端与客户端、分布式系统 |
| 与传统方案对比 | **Dual-Path**（上：传统失败路径，下：本文增强路径） | 防御 vs. 无防御 |
| 攻击者、受害系统与防御的交互 | **Threat Model**（信任边界框住受害系统；攻击者在边界外；有防御时用 Dual-Path 对照有/无防御两条路径） | 越狱攻击与防御、提示注入 |

风格档案中 `layout` 的取值 `pipeline`、`layered`、`hub_and_spoke`、`dual_path`、`threat_model` 分别对应上表五行。

### 2.2 现代简约风格（Modern Minimal）

- 浅色低饱和填充（灰白、浅天蓝），深色细边框 0.8–1.2 pt，微圆角；**NEVER** 使用 3D、渐变、阴影、光晕。
- 角色边界（如 Client / Server）用浅色虚线大框隔离并标注角色名。
- 关键数据流用带圈编号 ①–⑥ 标注，徽章放在箭头中段或框外缘，**NEVER** 遮挡模块文字；方法章节正文逐一引用编号（*"As depicted in step ③ of Fig. 2, …"*）。
- 本文核心模块用强调色（蓝 `#0072B2`），基线/对抗实体用朱红 `#D55E00`。
- 字号、线宽、圆角、填充深浅、分组框线型和各角色颜色由领域风格档案 `references/figure_styles/<domain_id>.json` 决定（如安全类论文强调信任边界与攻击者，系统类论文用实线分层框）；**NEVER** 在 spec 里硬编码颜色或线宽。档案中 `provisional` 下的值来自自进化循环，仅有一篇范文支持。

### 2.3 用脚本生成

把图写成 JSON 规格（格式见 `assets/architecture_example.json`），再运行：

```bash
uv run <skill_dir>/scripts/gen_architecture_diagram.py --spec fig_arch.json \
    --style <domain_id> --venue <venue> --out fig_arch.pdf
```

`role` 取值：`core`（本文模块）、`support`（服务端/辅助）、`adverse`（攻击/约束）、`neutral`（数据/通用组件），颜色取自风格档案的 `roles`。边的 `step` 字段生成编号徽章。档案的 `layout` 值是该领域的默认拓扑（§2.1），内容需要时可以换。`--validate-style <domain_id>` 只检查档案是否在 `_bounds.json` 范围内。

方框之外的元素（字段名与完整说明见脚本 docstring）：

| 需要表达 | 写法 |
| :--- | :--- |
| 攻击者、用户、模型、防御、文档、数据库等**参与方** | 方块加 `"shape": "actor_attacker"`（另有 `actor_user`、`model`、`shield`、`document`、`database`），图形按角色着色，标签在下方，箭头连到图形 |
| 总览图中的**关键测量曲线** | 先用 `plot_data_curves.py` 出图，再在方块中写 `"image": "curve.pdf"`（保持宽高比，标签在下方） |
| **攻击变体示例**（干净 vs. 降质输入） | 分组加 `"images": [{"path", "label"}, ...]` 与 `"cols"`，生成等大网格；有害内容先打码 |
| 攻击边、控制边 | 边加 `"role": "adverse"`（例如中性载荷发出的攻击边）与 `"line": "dashed"\|"dotted"` |

多条箭头汇入方块同一侧时会自动沿该侧错开；需要手动控制时用 `offset` 或 `from_side`/`to_side`。

### 2.4 自检清单

- [ ] 模块排列符合信息流向（左→右或下→上）；
- [ ] 每个关键步骤都有 ①–⑥ 编号且未遮挡文字；
- [ ] 角色边界用虚线框隔离；
- [ ] 除强调模块外均为柔和浅底色；
- [ ] 参与方用 `shape` 图形与数据、模块区分；需要证据的测量或示例用 `image` / `images` 放进图中，**NEVER** 用文字框代替曲线；
- [ ] 分组要么互不相交，要么带边距完整嵌套；箭头不穿过无关方块、分组或分组标题（脚本会报告）；
- [ ] 导出矢量 PDF，并通过 `check_figure.py`；
- [ ] 方法章节正文与图中编号一一对应。

---

## 3. 实验数据图

### 3.1 选择图表类型

| 实验目标 | 图表类型 | 要素 | 脚本 |
| :--- | :--- | :--- | :--- |
| 收敛速度、多轮精度 | 折线图 | 均值实线 + `fill_between` 标准差阴影 | `plot_data_curves.py` |
| 消融：组件贡献 | 分组柱状图 | 误差棒 + 相对完整模型的增量标注 | `plot_bar_ablation.py` |
| 超参数敏感性 | 折线图（x 为参数值） | 标出倒 U 型最优点 | `plot_data_curves.py --mark-best` |
| 两阶段扰动测试 | 折线图 | 竖向虚线分隔 Phase I / II | `plot_data_curves.py --phase-split X` |
| 跨骨干网方差 | 分组柱状图 / 箱线图 | 突出本文方法的小方差 | `plot_bar_ablation.py` |
| 高维表征聚类 | t-SNE / UMAP 散点 | 簇边界 + 高对比标记 | 无现成脚本：按 §1 规则写，并调用 `pubstyle.apply_style()` |
| 同一输入施加处理前后（如防御） | 成对柱状图 | 每组一个色相；处理前实心在前、处理后浅色斜纹在后；箭头 + 变化量 | `plot_bar_ablation.py --paired BEFORE AFTER` |
| 多模型 × 条件扫描（如分辨率） | 小多图（small multiples） | 共享坐标轴；对数/反向 x 轴；阴影标出关键区间 | `plot_data_curves.py`（CSV 加 `panel` 列）`--logx --invert-x --band X1 X2 LABEL` |
| 示例输入（干净 vs. 攻击/退化） | 图片网格 | 等大单元格、保持纵横比、下方标签；有害内容先打码 | `compose_examples.py` |

### 3.2 数据格式（长表 CSV）

- 曲线：`method,x,seed,value`（示例 `assets/curves_example.csv`）。脚本按 `method, x` 分组计算均值与标准差。
- 柱状图：`group,variant,seed,value`，或已汇总的 `group,variant,mean,std`（示例 `assets/ablation_example.csv`）。

```bash
uv run <skill_dir>/scripts/plot_data_curves.py --data results/curves.csv --ours "FedPE (Ours)" \
    --xlabel "Communication rounds" --ylabel "Test accuracy (%)" --out fig_convergence.pdf
uv run <skill_dir>/scripts/plot_bar_ablation.py --data results/ablation.csv --ours "Full model" \
    --ylabel "Accuracy (%)" --annotate-delta --out fig_ablation.pdf
uv run <skill_dir>/scripts/plot_bar_ablation.py --data results/defense.csv --paired "No defense" "With defense" \
    --ylabel "ASR" --venue acl --out fig_defense.pdf
uv run <skill_dir>/scripts/plot_data_curves.py --data results/sweep.csv --logx --invert-x \
    --band 30 90 "vulnerable band" --adverse ASR --ncols 4 --venue acl --out fig_sweep.pdf
uv run <skill_dir>/scripts/compose_examples.py --images clean.png blur.png --labels "Clean" "Blur" \
    --venue acl --out fig_examples.pdf
uv run <skill_dir>/scripts/check_figure.py --venue acl fig_*.pdf
```

### 3.3 尺寸与字号

宽度由 `--venue` 决定（数据在 `references/venues.json`；`--layout single` = 一栏宽，单栏会议中即正文宽；`double` = 正文宽）：

| 会议 | 栏数 | 单栏宽 | 正文宽 | 图 / 表 Caption |
| :--- | :--- | :--- | :--- | :--- |
| `ieee` | 2 | 3.5 in | 7.16 in | sentence / Title Case |
| `acm` | 2 | 3.33 in | 7.0 in | 全篇统一即可 |
| `acl` | 2 | 3.03 in | 6.30 in | sentence / sentence |
| `icml` | 2 | 3.25 in | 6.75 in | sentence / sentence |
| `usenix` | 2 | 3.33 in | 7.0 in | sentence / sentence |
| `neurips`, `iclr` | 1 | 5.5 in | 5.5 in | sentence / sentence |
| `lncs` | 1 | 4.8 in | 4.8 in | sentence / sentence |

高度：单栏图 2.2–2.6 in，跨栏图 2.5–3.5 in，小多图每行约 1.7 in。

字号（单栏 3.4 in 下与 9–10 pt 正文协调）：子图标题 10 pt 粗体，坐标轴标签 9 pt，刻度 8 pt，图例 7.5–8 pt，图内批注 7–8 pt；数学字体用 STIX。

### 3.4 Okabe-Ito 色值

| 名称 | HEX | 语义 |
| :--- | :--- | :--- |
| blue | `#0072B2` | 本文方法 |
| orange | `#E69F00` | 主要基线 |
| bluish_green | `#009E73` | 变体 / 支撑组件 |
| vermilion | `#D55E00` | 攻击 / 退化 |
| reddish_purple | `#CC79A7` | 次要基线 |
| sky_blue | `#56B4E9` | 辅助 / 轻度对比 |
| yellow | `#F0E442` | 特殊标注（慎用，白底对比度低） |
| black | `#000000` | 参考线 / 极端基线 |

---

## 4. 表格

- **MUST** 由脚本直接读取实验结果生成 `.tex` 表格源码，**NEVER** 手工抄数（保证逐字节可复现）。
- 表头尽量短；用 `\cmidrule(lr){...}` 划分分组；适配栏宽。
- 所有表格中基线的出现顺序全篇一致；本文方法所在行统一浅底色（`\rowcolor`）。
- 最优值用统一宏（如 `\best{...}`）标注，并在表标题或表注中说明规则；标准差统一为 `{\tiny$\pm$}` 格式；异常离散度在表注中解释（如 *"Std at most 4.9 except † (5.1–30.6)"*）。
- 表格编号与正文首次引用顺序一致；需要时调整 `\begin{table}` 在源码中的先后位置。

---

## 5. Caption

### 5.1 规则

- 大小写随会议（§3.3 表格）：IEEE 图用 Sentence case、表用 Title Case；ACL/NeurIPS/ICML 等图表都用 Sentence case。`lint_paper.py --venue <venue>` 按会议检查（W201/W202）。
- Caption 只说明：展示了什么、坐标轴与图例含义、数据集与模型（如 *"CIFAR-10 (CNN)"*）、统计口径（如 *"mean ± std over three seeds"*）、攻击注入轮次、虚实线含义。
- 结论是否进 Caption 由会议的 `caption_content` 决定（§0）：`neutral` 会议 **NEVER** 在 Caption 中下结论（*outperforms*, *superior*, *demonstrates*, *shows that*, *clearly*, *significantly better*），结论留给正文（W203）；`takeaway` 会议以一句要点开头，但要点必须有图中数据支撑，且不用 *significantly* 之类的强化词（W204 检查首句长度）。
- `\label` 必须放在 `\caption` 之后，否则编号错误（E001）。

### 5.2 示例

| | 图 Caption |
| :--- | :--- |
| ❌ | *Fig. 3. Accuracy Comparison Of Different Methods, Which Shows That Our Method Is Much Better.* |
| ✅ | *Fig. 3. Test accuracy over communication rounds on CIFAR-100 under Dirichlet non-IID partitioning (α = 0.1). Lines show the mean over three seeds; shaded areas denote one standard deviation.* |

| | 表 Caption |
| :--- | :--- |
| ❌ | *Table 2. accuracy of methods (ours is best)* |
| ✅ | *Table 2. Test Accuracy (%) of Different Methods on Dirichlet Non-IID Partitions. Best Results Are in Bold.* |
