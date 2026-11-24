# Two-Column Layout & Float Placement（双栏排版与浮动体）

> 适用：检查或修复图表位置、栏底空白、页数超限。**MUST** 用 `scripts/layout_check.py` 测量，**NEVER** 凭目测或推理判断浮动体落在哪一页。

---

## 1. 三条铁律

| 编号 | 规则 | 检测 |
| :--- | :--- | :--- |
| **R1** | 浮动体与其正文首次引用**同页**，且在阅读顺序上**先于**引用（同栏在上方；引用在右栏时可在左栏；跨栏图在页顶）。 | `check_layout.py` → `FAIL`（落后一页以上）/ `WARN`（同页但在引用之后、或提前一页） |
| **R2** | `figure*` / `table*` 最早出现在**定义处的下一页**，所以首次引用必须落在那一页或之后。推论：跨栏浮动体**永远不能出现在第 1 页**——第 1 页的预告图（teaser）必须用单栏 `figure`，或把它的首次引用放到第 2 页。 | `FAIL`，并提示把 `\begin{figure*}` 至少提前一页；首次引用在第 1 页时额外说明上述推论 |
| **R3** | 除末页外，栏底不得出现超过 1.5 行的空白。 | 日志中的 `Underfull \vbox ... while \output is active`（启发式，需目视确认） |
| **R4** | 正文（到参考文献或附录开始处）不超过会议页数限制。 | `layout_check.py --venue <venue>`（或 `--page-limit N`）报告 `Main body: X.XX pages` 与 `ok/FAIL page budget` |

另外：表格编号与首次引用顺序一致；从未被引用的浮动体（`WARN: never referenced`）要么补引用，要么删除。

---

## 2. 测量流程（确定性）

```bash
# 1) 修改前：记录基线（在论文目录外的 build/ 中编译，不改动源码）
uv run <skill_dir>/scripts/layout_check.py paper/main.tex --save-baseline layout_baseline.json
# 2) 修改正文
# 3) 修改后：与基线对比；FAIL 增加或某个浮动体变差时退出码为 1
uv run <skill_dir>/scripts/layout_check.py paper/main.tex --compare layout_baseline.json
```

- 引擎：默认 `pdflatex`，用 `--engine xelatex|lualatex` 与论文实际编译方式保持一致（引擎不同会改变排版）。
- 参考文献：如果论文目录中没有与 `.bib` 一致的 `main.bbl`，加 `--bibtex`（或 `--biber`），否则参考文献缺失会改变页数与浮动体位置。
- `floatcheck.sty` 通过 `TEXINPUTS` 加载，只写入 whatsit，不改变版面；`layout_check.py` 会比较带/不带该宏包的页数，若不一致会提示。
- 会议与页数：加 `--venue <venue>`（`references/venues.json`）。正文长度按参考文献/附录开始的位置计算到小数页；超过限制时退出码为 1，余量不足半页时提示风险。ACL 的 Limitations / Ethics 若放在参考文献之前会被一起计入，实际正文更短。

### 2.1 会议模板或字体缺失时（MUST 先确认）

`check_env.py --for layout --venue <venue> --paper-dir paper/` 会检查会议的类/样式文件与正文字体（包括字体文件本身，不只是宏包）。缺失时：

1. 优先把官方样式文件复制到 `main.tex` 旁边（ACL 的样式文件不在 TeX Live 中），安装字体（如 `tlmgr install newtx`）。
2. 无法获得时，用替代版式编译：版心、栏宽、字号与会议一致，正文用 Times 类字体；`layout_check.py` 会提示这只是估计。
3. 估计值至少留 **半页** 余量，并在报告中写明“页数为替代版式下的估计”。

---

## 3. 修复阶梯（按优先级，**NEVER** 用 `\vspace` / `\enlargethispage` / 手动 `\newpage` 硬挤）

1. **移动浮动体定义位置**：把 `\begin{figure}[t]` 在源码中提前或延后约半页；在当前栏构建过程中定义的 `[t]` 浮动体常被放到当前栏或下一栏顶部。
2. **移动首次引用**：把引用移进更合适的句子，例如节首总述句 *"… (Tables 8 and 9), and the flips are stable (Table 10)."*
3. **调整段落顺序**：让引用所在段落落到正确页面，并检查 *again / also* 等回指词是否仍然成立。
4. **补充有实质信息的句子**：仅在确实增加信息时使用（如解释某个例外的原因）。

**振荡（Oscillation）**：浮动体换页把引用段落推到另一页，来回跳动。处理：把首次引用移到远离分页边界的稳定位置（小节首句或段落末句）。

**版面补偿**：删减段末只剩 1–2 个词的行（孤行），每消除一个即可收回一行高度；改写时优先选择与原句等长的版本。孤行无法从日志检测，**MUST** 在 PDF 中目视检查。

---

## 4. 示例

| | 修复 R1（Table 3 落在引用的下一页） |
| :--- | :--- |
| ❌ | 在 Table 3 前插入 `\vspace{-2em}`，或把 `[t]` 改成 `[H]` 强制放置。 |
| ✅ | 把 `\begin{table}[t]` 从 §5.3 第 2 段之后移到 §5.3 开头之前；重跑 `layout_check.py --compare`，确认 `tab:main` 变为 `ok` 且其他浮动体没有变差。 |

---

## 5. 每次修改后的检查

- 每次改动正文后重跑 `layout_check.py --compare`：删减文字同样会让版面整体上移，导致多个浮动体错位。
- 用脚本或批量替换改写整段时，确认没有误删夹在段落之间的浮动体定义（`lint_paper.py` 会报告浮动体数量变化之外的引用缺失：E003）。
- 有页数上限时，每次修改后核对页数（`layout_check.py` 会打印总页数）。
