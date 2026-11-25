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
| W203 | warn | `neutral` 会议的 Caption 中下结论（会议由 `venues.json` 的 `caption_content` 决定） | 删除结论性措辞，把结论移到正文 |
| W301 | warn | 负 `\vspace` / `\vskip` / `\enlargethispage` | 删除，改用 `layout_and_typesetting.md` §3 的修复阶梯；用户坚持保留时记录原因 |
| W302 | warn | 模糊/防御性措辞 | 删除或替换为具体数字与事实（见 `writing/principles_and_style.md` §3） |
| W303 | warn | 段落堆砌数字 | 改写为“总—分—归因”：保留最难任务的 1–3 个数字与领先区间（见 `writing/evaluation.md` §2.6.4） |
| W304 | warn | `Fig. \ref` 使用可断行空格 | 改为 `Fig.~\ref{...}` |
| W305 | warn | 过度断言（*proves, conclusively, confirms that, undoubtedly* …，形式化证明环境除外） | 按 `writing/evaluation.md` 的归因证据阶梯改写：有消融/对照才用因果措辞，只有相关证据用 *is consistent with*，否则写成假设 |
| W204 | warn | `takeaway` 会议（NeurIPS/ICML/ICLR）Caption 首句超过 20 词 | 首句改为 3–12 词的要点句，再逐面板说明（见 `figures_and_captions.md` §0） |
| W306 | warn | 套话/机器腔（*has attracted increasing attention*, *delve*, *pivotal*, *seamlessly*, *simple yet effective* …） | 换成具体事实：谁、在什么条件下、差多少 |
| W307 | warn | 工作流痕迹（*supplied*, *the provided results*, *according to the notes*, `[intro.gap]` 之类的标签、箭头 →） | 以作者口吻重写，删除标签；正文不提“给定的输入” |
| W308 | warn | *Unlike X, we …*（拿方法和作者比较） | 改为 *Unlike X, our method …* |
| W309 | warn | *although …, but …* | 删掉 *but* |
| W310 | warn | 与范例库（`references/exemplars/`）共享 ≥ 6 个连续词 | 范例只学结构与节奏，重写该句 |
| W401 | warn | 摘要不在 150–250 词 | 按 5 句骨架增删（见 `writing/abstract_and_introduction.md`） |
| W402 | warn | 结论不在 120–200 词 | 两段式：总结 + 具体的未来方向（见 `writing/discussion_conclusion_ethics.md`） |
| W403 | warn | 会议要求的章节缺失（`--venue`，如 ACL 的 Limitations） | 按 `references/venues.json` 中该会议的 `required_sections` 补上 |

## check_bib.py（`.bib` 检查）

| 代码 | 级别 | 含义 | 修复 |
| :--- | :--- | :--- | :--- |
| B001 | error | 重复 key | 合并为一条，统一所有 `\cite` |
| B002 | error | 引用的 key 不在 `.bib` 中 | 补充条目（来源必须可核验），或修正 key 拼写 |
| B003 | error | 缺少必填字段 | 从出版方页面/DBLP 补全；**NEVER** 凭记忆编造 |
| B004 | error | 作者字段写了 `et al.` | 列出全部作者；确实过长时用 `and others` |
| B005 | error | 占位条目（TODO / FIXME / XXX / TBD / ?? 出现在字段或 key 中） | 换成核实过的真实条目；无法核实时向用户列出，**NEVER** 留占位条目投稿 |
| B101 | warn | 不同 key 的标题相同 | 确认是否同一篇（预印本与正式版），保留正式版 |
| B102 | warn | 年份不是 4 位数字 | 改为出版年份 |
| B103 | warn | 标题中的缩写/大小写混合词未加花括号 | 写成 `{FedAvg}`、`{IID}` |
| B104 | warn | arXiv/CoRR 预印本 | 查 DBLP/Google Scholar 是否已正式发表，若有则改引正式版 |
| B105 | info | 条目从未被引用 | 一般无需处理；清理前询问用户 |
| B106 | warn | `@misc` 没有 url / doi / eprint / howpublished，读者无法找到来源 | 补上可定位的来源字段，或改用正确的条目类型 |

## check_figure.py（图 PDF 检查）

| 代码 | 级别 | 含义 | 修复 |
| :--- | :--- | :--- | :--- |
| F1 | error | 宽度不符合会议的单栏/跨栏规格（`--venue`；默认 IEEE） | 用绘图脚本 `--layout single`（或 `double`）`--venue <venue>` 重新生成；**NEVER** 用 `bbox_inches="tight"`，也不要在 LaTeX 中缩放 |
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
| `FAIL page budget` | 正文超过页数限制 | 删减正文（先删重复与次要内容），把细节移入附录；每次修改后重跑 |
| `[warn] <class> is not installed` | 会议模板缺失，页数与浮动体位置只是估计 | 见 `layout_and_typesetting.md` §2.1 |
| 退出码 2 | 诊断编译失败 | 先让论文能正常编译；查看打印的 LaTeX 错误 |

## gen_architecture_diagram.py（架构图）

| 输出 | 含义 | 修复 |
| :--- | :--- | :--- |
| `[issue] ... overlaps ...` | 标签、编号徽章、模块文字或分组标题相互重叠 | 调整模块位置、边的 `offset` 或缩短文字 |
| `[issue] ... wider than ...` | 文字比所在模块或分组宽 | 加宽模块/分组或缩短文字 |
| `[issue] ... beyond the canvas` | 文字超出画布 | 缩短文字或扩大 `canvas` |
| `[issue] canvas aspect ...` | 画布比例与图尺寸不符，模块会被拉伸 | 按提示调整 `canvas` |
| 退出码 1 | 存在以上任一问题（图仍会生成，便于查看） | 修好规格后重新生成，直到退出码为 0 |
