# 参考文献规范与多源核验（Bibliography）

> 适用：整理或核对参考文献。先运行 `scripts/check_bib.py` 处理确定性问题，再按本文件逐条人工/联网核验。

## 五、参考文献规范与多源校验（Bibliography Verification）

### 5.1 多源核验与常见避坑清单
1. **多源自动化校验管道**：
   - 有 DOI 文献：调用 Crossref 官方 REST API（`api.crossref.org/works/<doi>`）自动化核对标准题录；
   - 无 DOI 顶会文献（NeurIPS/ICML/ICLR/USENIX）：经由 OpenAlex、DBLP、PMLR 官方页交叉验证。
2. **四大经典隐蔽 Bug 避坑清单**：
   - **作者姓与名颠倒**：将 `Kannan, Ramchandran` 误录为 `Ramchandran, Kannan`，导致正文缩写成了错误的 "R. Kannan"；
   - **纸质刊号年份 vs 网络首发年份脱节**：优先采用官方正式印刷出版年份；
   - **起止页码相差 1 页**：以官方收录的最终版 PDF 物理页码为唯一真值；
   - **会议集 Proceedings 命名年份与开会年份歧义**：严格遵循出版物正规标题中的版权年份，保持全文统一。

### 5.2 格式规范与战略引用
- **期刊与会议缩写全局一致**：严格遵循 IEEE 标准缩写规范（*IEEE Trans. Inf. Forensics Security*, *Proc. IEEE S&P* 等），绝不混用全称与缩写。
- **超长作者列表压缩**：在 `.bib` 头部配置 `IEEEtranBSTCTL` 控制文件，设置作者超标时自动折叠为 `"et al."` 压缩行数。
- **战略性文献引用**：在相关工作与对比中，有意识地检索并引用**目标期刊/目标会议近两年内发表的高质量相关成果**，精准迎合潜在审稿人圈层。
