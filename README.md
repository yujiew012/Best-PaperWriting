# Best-PaperWriting：计算机顶会/顶刊论文写作与学术绘图 Agent Skill

[![Skill: top-tier-paper-writing](https://img.shields.io/badge/Agent%20Skill-top--tier--paper--writing-blueviolet.svg)](skills/top-tier-paper-writing/SKILL.md)
[![Format: Agent Skills](https://img.shields.io/badge/Format-Agent%20Skills%20(SKILL.md)-blue.svg)](https://agentskills.io/specification)
[![Agents: Claude Code | Codex | Antigravity](https://img.shields.io/badge/Agents-Claude%20Code%20%7C%20Codex%20%7C%20Antigravity-brightgreen.svg)]()

`top-tier-paper-writing` 是一个通用的 **Agent Skill**：一个包含 `SKILL.md`、脚本与参考资料的文件夹，遵循开放的 Agent Skills 格式，可直接被 **Claude Code、OpenAI Codex、Google Antigravity（App 与 CLI）** 等编码 Agent 加载。

它从“发表过多篇顶会/顶刊的资深博士生与审稿人”视角，覆盖计算机论文（CCF-A 会议、IEEE/ACM Transactions）的完整生命周期：

1. **领域识别**：识别论文所属领域（安全、系统、机器学习、NLP/LLM），补齐该领域必备章节与图表；
2. **学术绘图**：现代简约架构图（带圈步骤编号 ①–⑥）与实验图（Okabe-Ito 色盲友好配色、单/双栏 3.4 / 6.9 in）；
3. **Caption 规范**：图用 Sentence case、表用 Title Case，Caption 不下结论；
4. **正文写作**：引言“双挑战—双案例—双直觉”，实验段落“总—分—归因”，拒绝报菜名；
5. **双栏排版**：浮动体三大铁律，配套 `floatcheck.sty` + `check_layout.py` 自动检查；
6. **句式库扩充**：从优秀范文中萃取因果归因句式，人工审核后写入；
7. **修订与投稿**：补实验后全文回溯、参考文献多源核验、arXiv 版本与期刊扩展投稿。

完整规范见 [`skills/top-tier-paper-writing/SKILL.md`](skills/top-tier-paper-writing/SKILL.md)。

---

## 一、安装

Skill 只有一份源文件：`skills/top-tier-paper-writing/`。安装脚本把它**链接**（默认）或**复制**到各 Agent 读取 Skill 的目录：

```bash
git clone https://github.com/yujiew012/Best-PaperWriting.git
cd Best-PaperWriting
python3 install.py                       # 为所有支持的 Agent 安装到用户目录
python3 -m pip install -r skills/top-tier-paper-writing/requirements.txt
```

安装后重启 Agent，让它重新扫描 Skill。常用选项：

```bash
python3 install.py --agent claude codex          # 只装给部分 Agent
python3 install.py --project /path/to/paper-repo # 装到某个论文项目里（可随项目提交）
python3 install.py --copy                        # 复制而不是链接（如 Windows 无法创建符号链接）
python3 install.py --dest /any/skills/dir        # 装到任意 skills 目录
python3 install.py --status                      # 查看安装状态
python3 install.py --uninstall                   # 卸载（只删除本脚本装的内容）
```

| Agent | 用户级目录（默认） | 项目级目录（`--project`） |
| :--- | :--- | :--- |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| OpenAI Codex | `~/.agents/skills/`（旧版本读 `~/.codex/skills/`，可用 `--dest` 指定） | `.agents/skills/` |
| Google Antigravity App | `~/.gemini/antigravity/skills/` | `.agents/skills/` |
| Google Antigravity CLI | `~/.gemini/antigravity-cli/skills/` | `.agents/skills/` |

- 默认使用符号链接，所有 Agent 共用同一份文件，`git pull` 后立即生效；用 `--copy` 时更新需重新运行安装。
- 各工具的目录约定仍在变化，如果你的版本读取其他位置，用 `--dest` 指定即可；安装后可在 Agent 中确认（Claude Code 和 Codex 用 `/skills`，Antigravity 看 Customizations 面板）。
- **其他 Agent**（不支持 Skill 的工具，如部分 IDE 助手）：`SKILL.md` 是普通 Markdown，可在项目的 `AGENTS.md` 或规则文件中写一句“写论文时先阅读 `<path>/top-tier-paper-writing/SKILL.md` 并按其中指引加载参考文件”。

### 使用

装好后，直接让 Agent 做论文相关的事即可，例如“帮我重写这篇论文的引言”“把这张实验表格写成分析段落”“检查一下 main.tex 的浮动体位置”。Agent 会根据 Skill 描述自动加载，也可以显式调用（Claude Code 中输入 `/top-tier-paper-writing`，Codex 中输入 `$top-tier-paper-writing`）。

---

## 二、目录结构

```
skills/top-tier-paper-writing/
├── SKILL.md                         # 总纲：工作流、各阶段规范、参考文件路由表
├── requirements.txt                 # 脚本依赖（matplotlib、numpy）
├── EVOLUTION_LOG.md                 # 句式库扩充记录
├── scripts/
│   ├── domain_adapter.py            # 领域识别（关键词打分 + 置信度）与领域配置生成，可选检索 arXiv
│   ├── self_evolve.py               # 从范文萃取候选句式，预览后 --apply 写入句式库
│   ├── plot_data_curves.py          # 多种子收敛曲线（阴影方差、IEEE 单栏）
│   ├── plot_bar_ablation.py         # 消融实验分组柱状图（误差棒、数值标注）
│   ├── gen_architecture_diagram.py  # 现代简约架构图（带圈编号 ①–⑥）
│   ├── floatcheck.sty               # 诊断编译用宏包：记录浮动体与 \ref 的页码和坐标
│   └── check_layout.py              # 检查浮动体三大铁律与日志中的版面警告
├── references/
│   ├── section_anatomy_guide.md     # 各章节宏观结构与段落解剖完整版、句子微雕、参考文献核验
│   ├── mechanism_sentence_bank.md   # “现象 → 归因 → 机制”句式库
│   ├── plotting_style_guide.md      # IEEE/ACM 图表尺寸、字号、配色速查
│   ├── domain_taxonomies.json       # 各领域必备章节、指标与图表偏好
│   ├── case_lessons_ieee_sp.md      # 案例：IEEE S&P 会议稿（LEVER）修改、排版与 arXiv 版本
│   └── case_lessons_ieee_tcc.md     # 案例：IEEE TCC 期刊稿（QEDFL）修改、参考文献与扩展投稿
└── templates/
    └── prompt_templates.md          # “实验表格 → 归因正文”“架构图设计”提示词模板
```

`SKILL.md` 只放总纲，详细内容放在 `references/` 中，Agent 进入对应步骤时才读取，避免一次占满上下文。

---

## 三、脚本速查

以下命令中的路径相对于仓库根目录；安装后也可以用安装位置的路径。

```bash
S=skills/top-tier-paper-writing/scripts

# 领域识别与配置（识别不确定时用 --domain 指定，离线时加 --offline）
python3 $S/domain_adapter.py --file idea.md --output session_domain_profile.json

# 绘图示例（以合成数据演示规范，替换为你的数据）
python3 $S/plot_data_curves.py --out fig_convergence.pdf
python3 $S/plot_bar_ablation.py --out fig_ablation.pdf
python3 $S/gen_architecture_diagram.py --out fig_architecture.pdf

# 浮动体检查：在论文目录中诊断编译两次（无需改源码），再检查
cp $S/floatcheck.sty /path/to/paper/ && cd /path/to/paper
pdflatex -jobname=main "\RequirePackage{floatcheck}\input{main}"
pdflatex -jobname=main "\RequirePackage{floatcheck}\input{main}"
python3 /path/to/Best-PaperWriting/skills/top-tier-paper-writing/scripts/check_layout.py main.aux

# 句式萃取：默认只预览，审核后加 --apply 写入句式库
python3 $S/self_evolve.py --file paper_mineru.md
python3 $S/self_evolve.py --file paper_mineru.md --apply
```

`check_layout.py` 的 `FAIL` 表示违反铁律（浮动体落后于首次引用页、`figure*` 定义太晚），`WARN` 表示同页但阅读顺序靠后或从未被引用；段末孤行无法从日志检测，仍需人工检查 PDF。

---

## 四、维护约定

- 只修改 `skills/top-tier-paper-writing/` 这一份源文件；不要在各 Agent 的安装目录里改（符号链接安装时它们就是同一份文件）。
- `SKILL.md` 保持在 500 行以内，细节写进 `references/`，并在 `SKILL.md` 的路由表中登记何时读取。
- frontmatter 的 `name` 必须与目录名一致，`description` 保持单行且不超过 1024 字符，否则部分 Agent 会拒绝加载。
