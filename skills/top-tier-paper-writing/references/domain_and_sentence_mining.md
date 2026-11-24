# Domain Profiling & Sentence Mining（领域识别与句式萃取）

> 适用：(a) 开始一篇新论文、需要确定领域必备章节与图表；(b) 用户提供优秀范文，希望扩充句式库。

---

## 1. 领域识别：`scripts/domain_adapter.py`

```bash
uv run <skill_dir>/scripts/domain_adapter.py --file idea.md --output session_domain_profile.json
uv run <skill_dir>/scripts/domain_adapter.py --text "backdoor defense for federated learning" --offline
```

- 按 `references/domain_taxonomies.json` 的关键词整词匹配打分，输出 `selection.confidence`。
- `confidence` 为 `low` / `none`（或退出码 1：无关键词匹配）时，**MUST** 向用户确认领域，再用 `--domain <id>` 重跑；**NEVER** 自行猜测。
- 结果中的 `tailored_guidelines` 用法：
  - `mandatory_sections`：检查论文是否包含（如安全领域的 *Threat Model*、系统领域的 *Testbed*）；缺失时向用户指出。
  - `recommended_plots`：选择实验图类型（见 `figures_and_captions.md` §3）。
  - `causal_mechanism_focus`：写归因句时使用的领域术语。
- arXiv 检索是按相关度排序的近 N 年同主题论文（无引用数），仅作结构参考；网络不可用时加 `--offline`。

## 2. 句式萃取：`scripts/self_evolve.py`（HITL）

```bash
uv run <skill_dir>/scripts/self_evolve.py --file paper_mineru.md            # 只预览
uv run <skill_dir>/scripts/self_evolve.py --file paper_mineru.md --apply    # 用户确认后写入
```

1. **MUST** 先不带 `--apply` 运行，把候选句原样展示给用户。
2. 只有用户明确同意后才加 `--apply`；写入 `mechanism_sentence_bank.md` 与 `EVOLUTION_LOG.md`。
3. 全文（MinerU Markdown）效果最好；`--arxiv_query` 只能拿到标题与摘要。
4. 候选来自关键词模式匹配，可能语义不当；与用户一起剔除不合适的句子（可在写入后手工删除对应行）。
