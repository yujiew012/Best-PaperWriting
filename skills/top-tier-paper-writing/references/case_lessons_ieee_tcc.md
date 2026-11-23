# 案例经验：IEEE TCC 期刊论文（QEDFL）

整理自 QEDFL 期刊稿（IEEE TCC，IEEEtran compsoc 模板）的修改、排版与投稿过程。按"写作 → 图表 → 排版 → 参考文献 → 投稿 → 工程习惯"的顺序组织，每条都尽量给出做法和原因。

---

## 1. 写作

### 1.1 补充实验后，全文同步检查旧表述

- 每加一组实验，都要回头通读全文，找出被新结果推翻或削弱的句子。
  - 例：6.1 节原本写"云端只接受格点值，所以恶意上传也被量化"。补做"跳过 SQ、自选格点值"的攻击者实验后，这句话就不成立了，必须改写。
- 要检查的位置包括：
  - 引言和贡献列表
  - 威胁模型
  - 理论部分的适用范围
  - 实验设置
  - 结论
  - 摘要里的数字
- 理论结论的适用范围也要随实验扩展。
  - 例：补充实验后，在命题后加了一句说明：逐坐标在两个相邻格点间独立取整的攻击者，上传服从 $Q(\mathbf{g}')$。因此检测极限同样覆盖这类攻击者，理论和实验对上了。

### 1.2 每句话要有明确主语

- 避免"Running the same detector…"这类读者要回头猜"谁的检测器、和什么相同"的写法，直接写成"Running QEDFL's detection on exact updates…"。
- 动名词作主语时，确认它指代清楚。
- "instead of"这类比较结构要挂在正确的成分上。
  - 例："A rule that rejects a fixed fraction of uploads instead of the robust threshold…"读起来很别扭。
  - 改成"Replacing the robust threshold of Phase 2a with a fixed rejection fraction…"就清楚了。

### 1.3 简洁

- 删掉重复前文结论的句子，例如前面已经给出数字，后面又写"Neither attacker is markedly stronger…"。
- 一个段落只讲一件事，用"结论句 + 证据（数字）"的结构。
- 长句拆成短句，并列成分超过三个时考虑分句。

### 1.4 用数字支撑比较，并诚实呈现对手的优势

- 某个基线在准确率上与我们相近时（如 LASA），不要回避。应指出我们在哪个维度更好，并给出可核对的区间。
  - 例："its FPR is 7.2–19.2% … against 2.2–12.9% for QEDFL"。
- 摘要、引言、结论和 README 里的关键数字必须一致，例如 4.7%、8.7–45.1%、9.3 ms。改一处就全局搜索一遍。
- 结论要写"在什么条件下成立"。例如"最差情况下"、"非 IID"、"三个随机种子取平均"。

### 1.5 回答"我们的方法是否仍有优势"

- 按数据集和攻击，分别列出每个防御方法的最差情况准确率，而不是只看平均值。
- 准确率之外，还要比较误报率（FPR）和开销，优势往往在这些维度。
- 只用实验数据下结论，不夸大。

---

## 2. 表格

- **用脚本生成，不要手抄数字。**
  - 例：`tables/make_main_table.py` 直接改写 tex 里的表格。
  - 改完脚本后，用它重新生成表格，确认与现有表格逐字节一致，才算脚本可信。
- **12 页版本用紧凑模式**（`--compact`）：缩写行名（如 "Trim. mean"），保证表格放得下。
- **最优值用统一的宏标出**，例如 `\best{}`（红色加粗），并在标题里说明标注规则。
- **标准差的写法：**
  - 统一用 `{\tiny$\pm$}`。
  - 标准差很大时，在标题里说明。例如："Std at most 4.9 except † (5.1–30.6)"。
- **表格标题用 IEEE 的 Title Case**，写清以下内容：
  - 指标和单位，如 "Test Accuracy (%)"
  - 实验设置，如 Non-IID、θ、α
  - 统计方式，如 "Mean Over Three Seeds"
  - 缩写，如 "MM: Min-Max, MS: Min-Sum"
- **"最差情况"表格要能用脚本复现。**
  - 例：`summarize_adaptive_attack.py` 在攻击方向 × 噪声配置中取均值最低的一组，并输出该点的标准差和 TPR。

---

## 3. 图

- **每张图都由脚本生成，并在 README 里记下生成命令和参数。** 例如 `--height 3.3 --attacks ALIE,MINMAX,MINSUM`，保证以后能原样重画。
- **矢量图放在 `paper/fig/`（PDF）。** 可编辑源文件放在 `paper/fig/src/`，例如架构图的 `.pptx`、流程图的独立 TikZ `.tex`。
- **全文版和 12 页版的图参数可以不同。** 例如更矮的高度、更少的子图，两套参数都要记录。
- **图标题用 IEEE 的 sentence case。** 写清以下内容：
  - 数据集和模型，如 "CIFAR-10 (CNN)"
  - 统计方式，如 "mean over three seeds"
  - 攻击从哪一轮开始
  - 曲线或虚线的含义
- **README 用的图单独导出 PNG**，放在 `docs/figures/`，并且按分支各自渲染（全文版和 12 页版不同）。
- **重画架构图时，不要沿用会议版的图。** 期刊扩展版的所有图表最好都是新的或重画的，这在差异说明里也是加分项。

---

## 4. 排版（IEEEtran / compsoc）

### 4.1 浮动体位置检查

- 用 `paper/tools/check_float_placement.py`，检查每个图和表与它第一次被引用的页码差：

  ```bash
  python3 paper/tools/check_float_placement.py paper /tmp/build
  ```

  > 该脚本位于 QEDFL 项目仓库中；本 Skill 的通用版本为 `scripts/floatcheck.sty` + `scripts/check_layout.py`（用法见 [`../SKILL.md`](../SKILL.md) 第七节）。

- **先记录基线，再改文字。** 比较方法是 `git stash` → 跑一次 → `git stash pop` → 再跑一次，对比两次输出。
- 本项目的基线：
  - 全文版（16 页）只有 fig:ratio 和 tab:noniid 落后一页。
  - 12 页版有 6 个浮动体落后。
- 任何改动都不能让落后的浮动体变多。

### 4.2 加字后的版面补偿

- **哪怕只加一句话，也可能把表格推到下一页。**
- **补偿办法：**
  - 改写成与原句等长的版本。
  - 删掉重复的句子。
  - 消除只有一两个词的段末孤行，这类改动最省空间。
- **12 页版本有硬性页数上限：** 每加一段，就要在别处删掉等量文字，改完立刻检查页数。
- **改写时优先选不改变行数的版本。**
  - 例："Quantization costs QEDFL almost no robustness: running its detection on exact updates instead changes…"
  - 这句和原句几乎等长。

### 4.3 其他排版要点

- 首页脚注（作者单位、基金、会议版说明）可能互相重叠，编译后要逐页目视检查。
- 每次改 tex 后都要重新编译并提交 PDF，否则仓库里的 PDF 会过期。
- 模板合规：
  - 使用 `\documentclass[10pt,journal,compsoc]{IEEEtran}`。
  - 关键词按字母顺序排列。
  - 页眉用 `\markboth`。

---

## 5. 参考文献

### 5.1 核对方法

- **有 DOI 的条目：** 用 Crossref（`api.crossref.org/works/<doi>`）逐项比对标题、作者、卷、期、页码和年份。
- **没有 DOI 的会议论文**（NeurIPS、ICML、AISTATS、USENIX、ICLR）**：** 用 OpenAlex，或者会议官网、PMLR、USENIX 页面核对。
- **注意：** Crossref 的模糊检索经常命中别的文章，结果不一致时，先确认命中的是不是同一篇论文。

### 5.2 本项目实际查出的错误类型

| 类型 | 例子 |
|---|---|
| 姓和名写反 | `Kannan, Ramchandran` 应为 `Ramchandran, Kannan`，正文里显示成了 "R. Kannan" |
| 年份与卷期不符 | ACM CSUR 第 57 卷第 4 期是 2025 年 4 月刊，在线发表却是 2024 年 |
| 页码相差 1 | Krum（NeurIPS 2017），最终按 OpenAlex 改为 118–128 |
| 会议年份有歧义 | ICPADS 的论文集名称是 2022，会议在 2023 年召开，两种写法都常见 |

### 5.3 格式

- 期刊名和会议名统一用 IEEE 缩写，例如 *IEEE Trans. Inf. Forensics Security*、*Proc. … (NeurIPS)*。
- 作者很多时用 `IEEEtranBSTCTL` 控制 "et al."，可以节省篇幅。
- 引用目标期刊（TCC）近两年的相关论文，体现论文和期刊范围的相关性。

---

## 6. 会议论文扩展投稿（IEEE CS 期刊）

### 6.1 投稿材料

| 投稿系统栏目 | 准备内容 |
|---|---|
| Main Manuscript | LaTeX 压缩包：主 tex、`sections/`、`.bib` 和已生成的 `.bbl`、`IEEEtran.cls/.bst`、所有图 |
| Previously Published – Statement | 新旧两版差异说明（PDF）：保留了什么、新增了什么，配逐项对比表 |
| Previously Published – Files | 会议原文 PDF |
| Cover letter | 1 页投稿信 |
| Image、LaTeX Supplementary、Tracked Changes | 首次投稿一般不需要 |

### 6.2 要点

- **压缩包必须在空目录里解压后能单独编译**，并且与本地 PDF 逐字比对一致。投稿时主文件选含 `\documentclass` 的那个 tex。
- **一定要附 `.bbl`**，有些系统不运行 BibTeX。
- **说明新内容的比例。**
  - 本项目查到的门槛是至少 35% 的新技术内容，这个数字来自搜索结果摘录，没能打开官方原文核实。
  - 可以用 8 词短语比对两版文本，量化文字重合度（本项目不到 1%）。
- **差异说明的写法：** 先列出"沿用的部分"，再用表格逐项对比，项目包括：
  - 场景
  - 威胁模型
  - 方法
  - 理论
  - 数据集
  - 攻击
  - 基线
  - 评测
- **作者有变动时**（增加或去掉作者），在投稿信里说明，并声明退出的作者知情且同意。最好事先留下他们的书面确认。
- **投稿信包含以下内容：**
  - 论文与期刊范围的契合点
  - 三条贡献
  - 扩展说明
  - 原创性、未一稿多投、全体作者同意、无利益冲突的声明
- **页数限制：** IEEE CS Transactions 正文上限 12 页（含参考文献和作者简介），超出部分每页收费。准备一个 12 页版本更稳妥。
- **关键词分类：** 选 2–10 个最贴切的。注意同名但含义不同的条目，例如 "I.4.1.c Quantization" 指图像量化，不适合本文。

---

## 7. 工程习惯

- **全文版和压缩版分两个分支维护**，例如 `main` 和 `compress-12pages`。同一处修改要在两个分支都做，各自检查版面。
- **用 git worktree 修改另一个分支，不切换当前工作区：**

  ```bash
  git worktree add <路径> <分支>
  ```

- **保持仓库整洁：**
  - 历史归档、引用的论文 PDF、编译中间文件都加入 `.gitignore`。
  - 脚本按用途放进 `tables/` 和 `figures/` 等目录，文件名能看出用途。
- **README 写清这些内容：** 项目简介、运行环境、运行命令、复现表格和图的命令、论文编译方法、引用方式。
- **私有仓库里可以放会议原文**（带出版商授权水印），但公开仓库之前要先删掉。
