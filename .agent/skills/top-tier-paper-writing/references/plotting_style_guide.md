# Academic Plotting & Visual Style Guide (顶会顶刊学术绘图视觉规范)

> 本规范对标 IEEE Transactions, ACM SIGCOMM/CCS, NeurIPS, ICML, ICLR 等顶级会议与期刊的排版与图形出版标准。

---

## 1. 物理尺寸规范（Dimensions & Aspect Ratios）

| 排版环境 | 推荐宽度 (Inches) | 推荐高度 (Inches) | 适用图表类型 |
| :--- | :--- | :--- | :--- |
| **IEEE/ACM 单栏图 (Single Column)** | 3.3 – 3.5 in | 2.2 – 2.6 in | 单折线收敛曲线、分组消融柱状图、超参敏感性分析 |
| **IEEE/ACM 双栏通栏图 (Double Column)** | 6.8 – 7.0 in | 2.5 – 3.5 in | 全景系统架构图、多数据集多子图并排 (1x3 或 1x4 Grid) |
| **1.5 栏或中等尺寸图** | 4.8 – 5.2 in | 3.0 – 3.4 in | 复杂聚类图、端到端混淆矩阵与热力图 |

---

## 2. 字号与排版层级（Typography Hierarchy）

在 3.4 英寸单栏宽度下，字体绝对不能过大或过小，必须与正文 9–10 pt 字号形成视觉协调：

- **子图标题 (Subplot Title)**: 9.5 – 10.5 pt (Bold)
- **坐标轴标签 (Axis Labels: X/Y)**: 9.0 pt (Regular)
- **刻度标签 (Tick Labels)**: 8.0 pt (Regular)
- **图例文本 (Legend Text)**: 7.5 – 8.0 pt (Regular)
- **图中批注与标记 (Annotations/Badges)**: 7.0 – 8.0 pt (Bold)
- **数学字体 (Math Text)**: 强制使用 STIX (`mathtext.fontset: 'stix'`) 或 Computer Modern，禁止默认无衬线字体。

---

## 3. Okabe-Ito (Wong) 色盲友好调色板代码速查

全球约 8% 男性与 0.5% 女性患有色觉障碍。使用以下 8 色标准代码可确保在全色觉谱系下均可清晰辨识：

```python
OKABE_ITO = {
    "blue":           "#0072B2",  # RGB(0, 114, 178)  - 自身主方法 (Primary Focus)
    "orange":         "#E69F00",  # RGB(230, 159, 0)  - 重点基线 1 (Key Baseline)
    "bluish_green":   "#009E73",  # RGB(0, 158, 115)  - 增强/对比变体 (Variant)
    "vermilion":      "#D55E00",  # RGB(213, 94, 0)   - 攻击/退化/受损状态 (Adverse)
    "reddish_purple": "#CC79A7",  # RGB(204, 121, 167)- 次要基线 2
    "sky_blue":       "#56B4E9",  # RGB(86, 180, 233) - 辅助背景/轻度对比
    "yellow":         "#F0E442",  # RGB(240, 228, 66) - 特殊标注点
    "black":          "#000000",  # RGB(0, 0, 0)      - 坐标轴基准线/极端基线
}
```

---

## 4. 架构图设计与审查清单（Architecture Diagram Checklist）

在绘制系统架构图（Figure 1 或 Figure 2）时，执行以下 6 项自检：
1. **[ ] 拓扑清晰**：模块排列是否符合信息流向（从左至右或从上至下）？
2. **[ ] 步骤编号**：关键数据流是否标注了带圈数字 ①–⑥？数字是否避开了框内文字？
3. **[ ] 模块解耦**：客户端与服务端的边界是否使用了虚线框（Dashed Box）明确隔离？
4. **[ ] 颜色克制**：除自身强调模块外，背景色是否采用了柔和低饱和度的浅底色（避免刺眼纯红绿）？
5. **[ ] 矢量输出**：是否直接导出了 `.pdf` 矢量格式并在正文 LaTeX 中通过 `\includegraphics` 引入？
6. **[ ] 正文呼应**：方法论章节（Method）正文中是否有显式语句与图中的编号步骤一一对应？
