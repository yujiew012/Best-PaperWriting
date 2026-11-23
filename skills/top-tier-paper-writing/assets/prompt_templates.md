# Prompt Templates for Top-Tier Paper Writing & Plotting

> 这些 Prompt 模板可以直接供 Agent 或研究者调用，用于自动化将“实验数据表格”转化为“深度机理分析正文”，以及指导绘制“现代简约学术架构图”。

---

## 模板 1：从原始实验表格到“深度机理归因”实验正文

```markdown
你是一位在计算机顶会（如 IEEE S&P / NeurIPS）和权威顶刊（IEEE Transactions）发表过多篇论文的资深学者与审稿人。
请阅读以下实验表格数据以及自研方法的核心机制，撰写该实验子节的分析正文：

【输入数据】：
- 数据集：[如 CIFAR-10, CIFAR-100]
- 对比基线：[如 Baseline A, Baseline B, Ours]
- 实验指标表格：[粘贴表格]

【自研核心组件与数学机理】：
- 组件 1（如 DDAP）：[作用：通过提示词自适应对齐新分布]
- 组件 2（如 PKM）：[作用：通过跨轮正则化惩罚突变，抑制特征被覆盖]

【写作硬性约束】：
1. 绝对不要逐行逐列读表（拒绝机械报菜名！审稿人自己会看表格）；
2. 严格遵循“总—分—归因”三步黄金段落法则：
   - 首句：直接给出该实验的最强宏观实证结论；
   - 中间句：仅挑选最复杂/最极限的数据集（如 CIFAR-100）列出 2–3 个关键数据和领先优势区间作为佐证；
   - 末尾句：深度解释“为什么会有这个优势”，强行将实证结果映射到组件 1 和组件 2 的具体数学操作与设计权衡上；
3. 使用成熟严谨的学术英语（Formal Register），穿插长短句。
```

---

## 模板 2：生成现代简约学术架构图（Architecture Diagram Prompt）

```markdown
请设计一个现代简约学术风（Modern Minimal Academic Style）的系统全景架构图（用于论文 Figure 2）：

【系统核心模块】：
1. 客户端边缘节点 (Edge Client)
   - 本地数据输入 (Input Data)
   - 动态自适应模块 (DDAP Module) -> 核心自研模块（重点突出）
   - 基础特征提取器 (Base Feature Encoder)
   - 联合判决头 (Classifier Head)
2. 中心聚合服务端 (Central Aggregation Server)
   - 模型聚合器 (Federated Aggregator)
3. 跨轮记忆正则约束 (Prior Knowledge Memory Regularizer)

【视觉与排版硬性约束】：
1. 风格：白底或极浅色底，圆角矩形，细深色边框（1.2pt），纯平面简约风格，严禁任何复杂 3D、炫目光晕或浓重阴影；
2. 颜色：遵循 Okabe-Ito 配色。自身核心自研模块使用 Deep Blue (#0072B2)，服务端使用 Forest Green (#009E73)，正则约束使用 Vermilion (#D55E00)；
3. 步骤引导：在数据流箭头上清晰标注带圈数字 ①, ②, ③, ④, ⑤, ⑥，徽章不可遮挡任何文本；
4. 边界解耦：客户端和服务端使用浅色虚线大外框（Dashed Bounding Box）物理隔离，标注角色名称。
```
