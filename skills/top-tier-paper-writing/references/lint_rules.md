# Checker Codes & Fixes（检查代码与修复方法）

> 适用：任一检查脚本报出代码时，按本表定位修复方法。修复后**重跑同一脚本**直到通过；同一问题连续 3 次修复失败时停止并向用户报告。

## lint_paper.py（`.tex` 静态检查）

| 代码 | 级别 | 含义 | 修复 |
| :--- | :--- | :--- | :--- |
| E001 | error | 浮动体主 `\label` 在 `\caption` 之前，编号会取错 | 把 `\label{...}` 移到 `\caption{...}` 之后（或放在 caption 参数末尾） |
| E003 | error | 引用了未定义的 label，或 `\input` 文件不存在 | 修正 label 拼写；确认被引用的浮动体/章节未被误删；补上缺失文件 |
| W002 | warn | 浮动体没有 `\caption` | 按 `figures_and_captions.md` §5 补写 Caption |
| W003 | warn | 浮动体没有 `\label` | 在 caption 后补 `\label{fig:...}` / `\label{tab:...}` |
| W101 | warn | 浮动体从未在正文被引用 | 在讨论它的句子中引用；若无处讨论，询问用户是否删除（删除需确认） |
| W201 | warn | 图 Caption 像 Title Case | 改为 Sentence case：仅首词与专有名词大写 |
| W202 | warn | 表 Caption 像 Sentence case（IEEE 要求 Title Case） | 实词首字母大写；ACM 等用 sentence case 的会议改用 `--caption-style sentence` |
| W203 | warn | Caption 中下结论 | 删除结论性措辞，把结论移到正文 |
| W301 | warn | 负 `\vspace` / `\vskip` / `\enlargethispage` | 删除，改用 `layout_and_typesetting.md` §3 的修复阶梯；用户坚持保留时记录原因 |
| W302 | warn | 模糊/防御性措辞 | 删除或替换为具体数字与事实（见 `writing/principles_and_style.md` §3） |
| W303 | warn | 段落堆砌数字 | 改写为“总—分—归因”：保留最难任务的 1–3 个数字与领先区间（见 `writing/evaluation.md` §2.6.4） |
| W304 | warn | `Fig. \ref` 使用可断行空格 | 改为 `Fig.~\ref{...}` |
| W401 | warn | 摘要不在 150–250 词 | 按 5 句骨架增删（见 `writing/abstract_and_introduction.md`） |
| W402 | warn | 结论不在 120–200 词 | 两段式：总结 + 具体的未来方向（见 `writing/discussion_conclusion_ethics.md`） |

## check_bib.py（`.bib` 检查）

| 代码 | 级别 | 含义 | 修复 |
| :--- | :--- | :--- | :--- |
| B001 | error | 重复 key | 合并为一条，统一所有 `\cite` |
| B002 | error | 引用的 key 不在 `.bib` 中 | 补充条目（来源必须可核验），或修正 key 拼写 |
| B003 | error | 缺少必填字段 | 从出版方页面/DBLP 补全；**NEVER** 凭记忆编造 |
| B004 | error | 作者字段写了 `et al.` | 列出全部作者；确实过长时用 `and others` |
| B101 | warn | 不同 key 的标题相同 | 确认是否同一篇（预印本与正式版），保留正式版 |
| B102 | warn | 年份不是 4 位数字 | 改为出版年份 |
| B103 | warn | 标题中的缩写/大小写混合词未加花括号 | 写成 `{FedAvg}`、`{IID}` |
| B104 | warn | arXiv/CoRR 预印本 | 查 DBLP/Google Scholar 是否已正式发表，若有则改引正式版 |
| B105 | info | 条目从未被引用 | 一般无需处理；清理前询问用户 |

## check_figure.py（图 PDF 检查）

| 代码 | 级别 | 含义 | 修复 |
| :--- | :--- | :--- | :--- |
| F1 | error | 宽度不符合单栏/跨栏规格 | 用绘图脚本 `--layout single|double` 重新生成；**NEVER** 用 `bbox_inches="tight"` |
| F2 | error | 含 Type 3 字体 | `pdf.fonttype=42`（`pubstyle.py` 已设置）后重新生成 |
| F3 | warn | 字体可能未嵌入 | 用脚本重新生成；外部工具导出时开启“嵌入全部字体” |
| F4 | warn | 位图包在 PDF 中 | 从源数据重新绘制矢量图 |

## check_layout.py / layout_check.py（浮动体位置）

| 输出 | 含义 | 修复 |
| :--- | :--- | :--- |
| `FAIL R1` | 浮动体在首次引用之后的页面 | `layout_and_typesetting.md` §3 修复阶梯，从第 1 级开始 |
| `FAIL R2` | `figure*`/`table*` 定义太晚 | 把 `\begin{figure*}` 移到首次引用所在页的前一页 |
| `WARN R1` | 同页但在引用之后，或提前一页 | 优先调整引用句位置 |
| `WARN never referenced` | 无正文引用 | 同 W101 |
| `R3 ... void` | 栏底可能有空白 | 在 PDF 中目视确认；用补偿技巧填充 |
| `REGRESSION` | 与基线相比变差 | 撤销最近一次修改或换一种修复方式，再次 `--compare` |
| 退出码 2 | 诊断编译失败 | 先让论文能正常编译；查看打印的 LaTeX 错误 |
