# Figures, Tables & Captions（图、表与 Caption）

> 适用：绘制架构图或实验图、设计表格、撰写/审查 Caption。
> 绘图一律通过 `scripts/` 中的脚本完成（样式由 `scripts/pubstyle.py` 统一注入），**不要**手写 rcParams 或手算统计量。

---

## 1. 硬性规则

1. **MUST** 使用真实实验数据作图；图中每个数字都能追溯到结果文件（在 LaTeX 源码注释中写明出处）。**NEVER** 用示例数据（`assets/*_example.*`、`--demo`）生成论文插图。
2. **MUST** 按版式定宽：单栏 3.4 in，跨栏 6.9 in（可接受 3.3–3.5 / 6.8–7.0 in），导出矢量 PDF（字体为 TrueType/Type 42 嵌入，无 Type 3）。用 `scripts/check_figure.py` 验证。
3. **MUST** 使用 Okabe-Ito 色盲友好调色板，并全篇固定语义：蓝 `#0072B2` = 本文方法，橙 `#E69F00` / 紫 `#CC79A7` = 基线，绿 `#009E73` = 变体/支撑组件，朱红 `#D55E00` = 攻击/退化/对抗实体。
4. **MUST** 黑白可辨：不同曲线同时使用不同标记（`o s ^ D v`）与线型（`- -- -. :`），脚本已自动分配。
5. **MUST** 多随机种子（≥ 3 seeds）报告均值 ± 标准差；曲线用阴影带，柱状图用误差棒。少于 3 个种子时脚本会警告，必须在 Caption 中说明种子数。
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

### 2.2 现代简约风格（Modern Minimal）

- 浅色低饱和填充（灰白、浅天蓝），深色细边框 0.8–1.2 pt，微圆角；**NEVER** 使用 3D、渐变、阴影、光晕。
- 角色边界（如 Client / Server）用浅色虚线大框隔离并标注角色名。
- 关键数据流用带圈编号 ①–⑥ 标注，徽章放在箭头中段或框外缘，**NEVER** 遮挡模块文字；方法章节正文逐一引用编号（*"As depicted in step ③ of Fig. 2, …"*）。
- 本文核心模块用强调色（蓝 `#0072B2`），基线/对抗实体用朱红 `#D55E00`。

### 2.3 用脚本生成

把图写成 JSON 规格（格式见 `assets/architecture_example.json`），再运行：

```bash
uv run <skill_dir>/scripts/gen_architecture_diagram.py --spec fig_arch.json --out fig_arch.pdf
```

`role` 取值：`core`（本文模块）、`support`（服务端/辅助）、`adverse`（攻击/约束）、`neutral`（数据/通用组件）。边的 `step` 字段生成编号徽章。

### 2.4 自检清单

- [ ] 模块排列符合信息流向（左→右或下→上）；
- [ ] 每个关键步骤都有 ①–⑥ 编号且未遮挡文字；
- [ ] 角色边界用虚线框隔离；
- [ ] 除强调模块外均为柔和浅底色；
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

### 3.2 数据格式（长表 CSV）

- 曲线：`method,x,seed,value`（示例 `assets/curves_example.csv`）。脚本按 `method, x` 分组计算均值与标准差。
- 柱状图：`group,variant,seed,value`，或已汇总的 `group,variant,mean,std`（示例 `assets/ablation_example.csv`）。

```bash
uv run <skill_dir>/scripts/plot_data_curves.py --data results/curves.csv --ours "FedPE (Ours)" \
    --xlabel "Communication rounds" --ylabel "Test accuracy (%)" --out fig_convergence.pdf
uv run <skill_dir>/scripts/plot_bar_ablation.py --data results/ablation.csv --ours "Full model" \
    --ylabel "Accuracy (%)" --annotate-delta --out fig_ablation.pdf
uv run <skill_dir>/scripts/check_figure.py fig_convergence.pdf fig_ablation.pdf
```

### 3.3 尺寸与字号

| 版式 | 宽 | 高 | 用途 |
| :--- | :--- | :--- | :--- |
| 单栏 | 3.4 in | 2.2–2.6 in | 单条收敛曲线、消融柱状图、敏感性分析 |
| 跨栏 | 6.9 in | 2.5–3.5 in | 全景架构图、1×3 / 1×4 多子图 |
| 1.5 栏 | 4.8–5.2 in | 3.0–3.4 in | 混淆矩阵、热力图、复杂聚类图 |

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

- 图标题 **IEEE Sentence case**（仅首词与专有名词大写）；表标题 **IEEE Title Case**（实词首字母大写）。`lint_paper.py` 会检查（W201/W202）。
- Caption 只说明：展示了什么、坐标轴与图例含义、数据集与模型（如 *"CIFAR-10 (CNN)"*）、统计口径（如 *"mean ± std over three seeds"*）、攻击注入轮次、虚实线含义。
- **NEVER** 在 Caption 中下结论（*outperforms*, *superior*, *demonstrates*, *shows that*, *clearly*, *significantly better*）；结论留给正文。`lint_paper.py` 会检查（W203）。
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
