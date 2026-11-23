# 顶会论文写作与图表经验总结

本文总结了 LEVER / Provenance Gate 论文（IEEE S&P 投稿版与 arXiv 版）修改过程中沉淀下来的写作、图表与排版经验。

每条经验都写成可复用的规则，并尽量附上本论文中的正反例。

---

## 一、总体原则

1. **表层流畅，底层严谨。** 主线叙事要让审稿人一口气读懂"为什么难、怎么解决、效果如何"。严谨性细节（样本量、版本、排除项、统计检验、保守下界的论证）放进表注、实验设置、有效性小节和附录。审稿人起疑时，翻过去就能找到。
2. **每句话都要有作用。** 一句话如果在正文别处已经说过、只是重述表格，或者只是在防御性地限定范围，就删掉或者挪走。
3. **用重点数据说结论。** 每段只报告支撑本段论点的一两个关键数字，其余数字交给表格。
4. **诚实优先于漂亮。** 数据不支持的说法不能写，哪怕它听起来更好。比如消融显示 feedback 和探索项作用很小，就不能写"每个组件都有用"，而应写成"lever 是核心，搜索不需要精细调参"。
5. **写之前先核对数据。** 运行示例、关键数字都要回到实验结果文件里核实。本论文的运行示例其实是唯一被 Gate *升级给人工*的条目（clean 分数恰好落在边界上），而不是被"拦截"的条目，写错了就会被抓。

---

## 二、各章节怎么写

### 1. Introduction

推荐的递进结构：

1. **背景与现象**：用一个具体例子（Fig. 1 的运行示例）引出问题。
2. **已有工作的不足**：给出量化证据。例如"最强的已有攻击有 99/125 次成功其实加入了新事实"。
3. **核心问题**：一句斜体的研究问题。
4. **挑战 C1–C3**：用 `\emph{C1: ...}` 的形式列出，每个挑战一句话说清为什么难。
5. **方法**：逐个说明方法的组件对应解决哪个挑战，并在句中标注 (C1)/(C2)/(C3)。
6. **防御与主要结果**：防御放在攻击之后，用 "we further propose" 引出，不要和"应对挑战"混在一起。挑战是攻击的挑战，防御是进一步的贡献。
7. **贡献列表**：四条，每条简洁：
   - (1) 我们发现了什么问题；
   - (2) 攻击方法是什么；
   - (3) 防御方法是什么、有什么保证；
   - (4) 效果（最核心的一两个数字）。
   - 不要写"as an independent check and a human audit confirm"这类证据说明，也不要罗列次要发现。

注意事项：

- 洞察句（例如"typed outputs stop injection but not persuasion"）必须紧跟支撑它的数据，并用 "These results show…" 显式衔接，否则会显得突兀。如果显得冗余，宁可删掉。
- 避免绕的句式。比如"we disclosed the attack to the developer of every model we attacked: …"，直接写成"We disclosed the attack to A, B, C, and D."

### 2. Method（方法论）

- **方法论里不出现实验设置。** 具体超参（c=0.5、λ=0.05、每条样本 100 次查询、40 次 writer 调用、温度等）放到 §6.1 Setup 和附录。方法里只写参数的*作用*，比如"A larger c explores rarely used levers more often"。
- 每个小节用 **Challenge → Approach** 组织（加粗的段首小标题），让读者一读就知道这一段要解决什么。
- 小节开头先把组件和挑战对应起来，例如"The levers … (C1), the verifier … (C1 and C2), and the search … (C3)"。

### 3. Defense（防御设计）

- 不要平铺直叙一堆规则，每段写**一个设计决策及其理由**。好的段首小标题示例：
  - *Why the gate always measures d_T*：先说明更便宜的替代设计有什么盲区，再说明我们为什么这样设计。
  - *Separating fact changes from rule changes*：rule probe 搭在同一次查询上，所以不增加成本，而且只用 typed question。
  - *Escalating what the model cannot decide*：落在边界上的答案交给人工。
- 段首小标题**不要和小节标题重复**。小节标题已经是 "Querying Again without Unauthorized Entries"，就不要再写 "Key idea: ask the model again…"。
- 先列出 **Design goals G1–G4**（integrity / utility / cost / deployability），再用一张对比表把各类已有防御放在这四个目标上比较（✓/✗），后文用 (G1)…(G4) 回扣。
- 安全保证小节先说"我们要证明什么、为什么重要"，再列假设（"First … Second …"），然后给出命题、证明，最后写"保证不覆盖什么"。

### 4. Evaluation（实验）

- **开头列 RQ1–RQ5**，小节标题写成 "RQ1: …"，并说明哪一小节回答哪个 RQ。
- **Setup 用加粗小标题组织**：Datasets / Target models / Attack configuration / Metrics。
- **段落是"总—分—总"结构**：
  - 首句：本段说明了什么结论；
  - 中间：一两个关键数字；
  - 末句：由此得出什么。
- **不讲实验是怎么构造的**（抽样、打乱、标注者看到什么等），这些交给附录。正文只说"这个实验说明了什么"。
- **按组件或检验分加粗小标题**，例如：
  - 消融：Levers / Criterion reframing / Verifier / Search；
  - 有效性：The checks are reliable / Comments add no facts / The flips are stable；
  - 防御：Replayed / Other models / Authorized fact changes / Adaptive。
- 每个子节**紧扣小标题**。例如 "Attack Effectiveness and Transfer" 下每段的主语都是我们的方法，删掉噪声对照这类无关句子。
- **统计说明放进表注**：例如"each defense is attacked once…; sign test p<0.03"写在表格 caption 里，而不是正文中间。
- 可以用斜体强调全节最重要的一句，但每节最多一句，例如"A defense that judges the attacker's text thus remains open to text written against it."
- 不需要单独的 "Takeaways" 小节，结论应该已经体现在各段的首句和末句里。

### 5. Discussion

Discussion 回答 **Why**，不重复 **What**。选 2–3 个核心模块，用加粗小标题组织，篇幅约 0.5–1 页：

- **机理（Why it works）**：剥离具体数字，讲清本质。比如 typed output 关闭了指令通道，却没有关闭解释空间，framing 利用的正是问题没有说清的部分。
- **可迁移的设计原则**：例如"Defend on provenance, not on content"，以及如何设计问题和评测来抵御 framing。
- **放松威胁模型**：如果核心假设被打破会怎样（无标签插入、授权来源被攻破、非确定性解码），以及**了解防御的自适应攻击者**最多能做到什么。
- **更广泛的影响**：方法如何延伸到 LLM-as-judge、内容审核、agent 工具调用审批等场景。
- **局限性要少而精**：一两句话界定范围，而不是道歉。例如"只评测了某个版本和英语，但命题 1 不依赖这些条件"。
- 自检标准：把方法名和表格遮住，同行仍然能从这一节学到东西。
- 伦理部分单独成节，不要放进 Discussion。

### 6. Conclusion

两段，约 120–200 词，是对全文的收束，**不是摘要的复制**：

1. **重新锚定问题**，从结论的视角写，而不是重新科普背景。
2. **核心机制**：讲因果逻辑，不罗列步骤。例如"LEVER exploits this room…; the Gate closes it…"。
3. **决定性证据**：只给一两个核心数字，用过去时或现在完成时（Abstract 是"预告"，Conclusion 是"定论"）。
4. **收尾**：落在一个设计原则或实际价值上，例如"Deciding on provenance rather than content…lays a practical foundation for…"。

禁忌：引入新数字、写局限性、写 "we hope…"、空泛的口号。

### 7. Ethics Considerations

- **Disclosure**：直接写明向谁披露。例如"We disclosed the attack to TypeSafe for Jev, Amazon Web Services for strands-decider…, Convai Innovations for laya, and the author of kev"。说明走的是哪类渠道（安全策略指定的渠道，没有就用直接联系方式）。个人开发者用角色称呼（the author of …），不写人名。
- 不写具体日期、请求数量等琐碎信息，也不写承诺性的协调细节（如"we offered the full logs…"）。
- 开发者有回复时，再补一句回复情况。

---

## 三、句子与用语

1. **语域正式**：不用口语化的动词和习语（selects / reduces / performs worse，而不是 picks / cuts / fares worse）。
2. **术语全文统一**，并维护一份术语表。例如：
   - "authorized fact change"，而不是 "authorized update"；
   - "correct decision"，而不是 "gold"；
   - 不把 clean decision 叫 "baseline"。
3. **句长**：超过约 40 词的句子要拆开。长短句交错，读起来才有节奏。
4. **引用位置**：句中间的 `(\cref…)` 尽量移到句末，不要打断阅读。
5. **不要机械的规则**：自然的复合形容词可以带连字符；连接词不设硬性上限，但避免反复使用同一个词。
6. **冠词**：正文用 "the Provenance Gate"；标题、图题、表格行名省略冠词（"Our Defense: Provenance Gate"，与 "Our Attack: LEVER" 并列）。
7. **字体**：模型名和版本号用正体，参数规模属于名字的一部分（`kev-0.8B`、`Gemma4-12B`），这与顶会论文的惯例一致。方法名用全大写正体（LEVER），正文中不用打字机字体。
8. **不要防御性限定**：作用范围交代一次即可，不要每句都加"under our threat model / on the items they share / unless the verifier errs"。

---

## 四、图表

### 1. 图的设计

- **概览图（Fig. 2）给出编号步骤** ①–⑥，caption 按编号逐步讲解流程，正文也可以引用这些步骤。编号标记放在模块边框上，避免与标题文字重叠。
- **运行示例贯穿全文**：Fig. 1、Fig. 2、§5 都用同一个例子，图中的数值必须来自真实运行结果（在源码注释里写明出处）。
- **配色全文统一**，并检查色盲友好：蓝色代表我们的方法，橙色代表已有攻击，红色代表攻击者写的文本。lever 用固定的四色。
- caption 说明"图/表展示什么、怎么读"，结论留给正文。

### 2. 表的设计

- **每张表都要适配栏宽。** 编译日志没有 Overfull 警告也不代表没问题，每次新增或修改表格后都要渲染出来看一眼。表头尽量短，用 `\cmidrule` 分组。
- 各表中模型的顺序保持一致。
- 我们的方法所在行用浅色底高亮（`\rowcolor`）。
- **对比表**：用 ✓/✗ 把已有防御放在我们定义的设计目标上比较，这能直观展示我们方法的定位。
- 统计说明、次要计数、协议细节放在表注或 caption 里（脚注用 ∗、†、‡）。
- **表格编号要和正文首次引用的顺序一致**。表格按定义顺序编号，需要时调整定义顺序。

---

## 五、排版规则（双栏）

### 1. 硬性规则

1. 每个图表都出现在**首次引用之前**（按阅读顺序），并且和首次引用**在同一页**。"之前"指：同栏的上方；首次引用在右栏时，图表可以在左栏；跨栏宽图在页顶。
2. 每页都要排满，栏底不能留大片空白，最后一页除外。
3. 跨栏浮动体（`figure*` / `table*`）最早出现在定义位置的**下一页**，所以它的首次引用必须落在那一页。

### 2. 检查工具

用 `\floatcheck` 构建，在每个浮动体处记录位置；再用 `scripts/paper/check_layout.py` 检查同页、顺序和空白。

已知的局限：脚本不识别 "Tables 8 and 9" 这类合并引用，会误报，需要人工核对位置。

### 3. 修复浮动体位置的手段（按优先级）

1. **移动浮动体的定义位置**（源码中的 `\begin{table}`）：在当前栏构建过程中定义的 `[!t]` 浮动体，常常会被放到当前栏或下一栏的顶部。
2. **移动引用位置**：把首次引用放进一个更合适的句子里，例如节首的总述句"…(Tables 8 and 9), and the flips are stable (Table 10)"。
3. **调整段落顺序**：让引用所在的段落落在正确的页面上，同时检查逻辑是否依然通顺（必要时改写"again / also"这类回指词）。
4. **补充有实质内容的句子**：只在确实增加信息时使用，例如解释为什么 sandwich 防御是例外、规则对照测量了什么。**不要用 `\vspace` 等硬性调整。**

### 4. 注意"振荡"现象

浮动体放到哪一页，就会把引用它的段落推到另一页。遇到这种情况，就把引用放到页面边界之外更稳定的位置，比如节首句或段落末句。

### 5. 每次修改后的检查

- 每次改动正文后都重跑布局检查。删减文字同样会让版面整体上移，导致多个浮动体错位。
- 用脚本替换整段文字时，要确认没有误删夹在段落之间的浮动体定义。本次就误删过消融表，靠检查发现后才恢复。
- 长期目标：主体篇幅符合会议页数限制，附录尽量不溢出到只有几行的新页面。

---

## 六、细节放在哪里

| 内容 | 放在哪里 |
| --- | --- |
| 研究问题、挑战、洞察、核心结果 | Introduction、各段首句 |
| 设计决策及其理由 | Method / Defense |
| 超参、预算、温度、模型版本 | §6.1 Setup（一句话）+ 附录设置表 |
| 基线的补丁、模板原文、防御提示词原文 | 附录 "Baselines and Defenses" |
| 人工标注流程、第二轮标注 | 附录 "Human Audit"，正文只放一个指针 |
| 统计检验、单次运行说明、计数 | 表注 / caption |
| 局限性 | Discussion 最后，一两句话 |
| 伦理、披露、标注者、AI 使用 | 单独的 Ethics Considerations 一节 |

---

## 七、arXiv 版本

1. **内容与投稿版保持一致**，只增加作者信息。作者信息会改变排版，修复错位时优先选择两个版本都能接受的改法（如调整段落顺序），让正文保持一致；只改引用位置的差异可以接受。
2. **arXiv 格式要求**：
   - 第一行写 `\pdfoutput=1`；
   - 用 `\thanks` 写单位时需要 `\IEEEoverridecommandlockouts`；
   - 删除源码注释（arXiv 会公开源码），但行末用来控制空格的 `%` 要保留；
   - 附带与 `.bib` 一致的 `main.bbl`（arXiv 不运行 BibTeX）；
   - 删除匿名开关，加上致谢。
3. **编译器选 pdflatex**：与 `\pdfoutput=1`、`fontenc/inputenc/mathptmx`、PDF 插图和 `\pdfsavepos` 一致。xelatex 会换字体、改变排版。
4. **提交前单独测试**：把 arXiv 文件夹复制到空目录中，在没有 `.bib` 的情况下编译，确认页数、引用和图表正常。
5. **元数据**：
   - 标题、作者、摘要用纯文本，宏要展开（`\jev` 写成 Jev）；
   - Comments 填"页数、图数、表数"；双盲审稿期间不写投稿会议名；
   - Journal reference、DOI、Report number 留空；
   - 主分类 cs.CR，交叉分类 cs.CL / cs.AI。

---

## 八、工作流程

1. 每次修改独立成一个分支和 PR，提交信息说明改了什么、为什么改，合并后确认远端与本地一致。
2. 每次修改后的检查清单：
   - 编译无错误；
   - 布局检查通过；
   - 新增或修改的表格渲染后目视检查；
   - 关键数字与结果文件核对；
   - 术语和禁用词检查。
3. 投稿版与 arXiv 版之间用"去注释后逐文件 diff"验证，差异只允许是预期中的引用位置调整。
