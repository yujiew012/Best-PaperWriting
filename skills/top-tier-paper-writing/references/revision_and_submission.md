# Revision, Verification & Submission（修订、核验与投稿）

> 适用：补实验后的全文修订、投稿前检查、准备 arXiv 版本或会议扩展期刊稿。具体正反例见两份案例：[`case_lessons_ieee_sp.md`](case_lessons_ieee_sp.md)（会议稿 + arXiv）、[`case_lessons_ieee_tcc.md`](case_lessons_ieee_tcc.md)（期刊稿 + 扩展投稿）。

---

## 1. 补实验后的全局回溯（MUST）

每加一组实验，通读以下位置，改写被新结果推翻或削弱的句子：引言与贡献列表、威胁模型、理论结论的适用范围、实验设置、结论、摘要中的数字。理论适用范围要随实验扩展同步更新（案例：`case_lessons_ieee_tcc.md` §1.1）。

| | 示例 |
| :--- | :--- |
| ❌ | 新增“攻击者跳过量化”的实验后，§6.1 仍写着“云端只接受格点值，所以恶意上传也被量化”。 |
| ✅ | 改为说明该假设不再成立，并在命题后补一句其对新攻击者同样适用的条件。 |

## 2. 数字与运行实例核对（MUST）

- 正文、摘要、Caption 中的每个关键数字都要回到实验结果文件核对；**NEVER** 编造、四舍五入后改变结论或沿用旧版本数字。
- 运行实例（Running Example）的描述必须与日志一致（案例：`case_lessons_ieee_sp.md` 第一节第 5 条）。
- 输出给用户时，列出“数字 → 来源文件”的对应关系。

## 3. 参考文献

先运行 `scripts/check_bib.py`（确定性检查），再按 [`bibliography.md`](bibliography.md) 逐条多源核验。

## 4. 版面回归

修改前后各运行一次 `scripts/layout_check.py`（`--save-baseline` / `--compare`），FAIL 不得增加；同时核对页数上限。

## 5. arXiv 版本

- 第一行 `\pdfoutput=1`；用 `\thanks` 写单位时需要 `\IEEEoverridecommandlockouts`。
- 删除源码注释（arXiv 公开源码），但保留行末用于控制空格的 `%`。
- 附带与 `.bib` 一致的 `main.bbl`（arXiv 不运行 BibTeX）。
- 编译器与投稿版一致（通常为 pdflatex）。
- 把 arXiv 文件夹复制到空目录，在没有 `.bib` 的情况下编译，确认页数、引用与图表正常。
- 元数据：标题、作者、摘要为纯文本（展开宏）；Comments 写“页数、图数、表数”；双盲期间不写投稿会议名。

详见 `case_lessons_ieee_sp.md` 第七节。

## 6. 会议论文扩展为期刊稿

投稿材料清单（Main Manuscript、Previously Published Statement、会议原文、Cover letter）、新内容比例的量化方法与差异说明表的写法，见 `case_lessons_ieee_tcc.md` 第 6 节。

## 7. 人工确认边界（HITL）

以下操作 **MUST** 先向用户展示并获得明确同意：提交到 arXiv/投稿系统、发送邮件、删除或批量改写已有章节、删除浮动体或参考文献条目、修改作者列表与致谢。Agent 只准备材料，**NEVER** 代替用户提交。
