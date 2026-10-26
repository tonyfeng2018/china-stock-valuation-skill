---
name: china-stock-valuation
description: Source-audited A-share stock fundamental research, policy and peer monitoring, multi-method valuation with pessimistic/base/optimistic reasonable market cap and share price, and Kimi/DeepSeek-compatible Chinese research reporting. Trigger for Shanghai/Shenzhen/Beijing equity reviews, earnings and valuation changes, sector comparisons, and investment risk events.
---

# 中国股票研究与估值 Skill v1.1

## 目标与底线
为沪深北证券提供 **公开证据 → 交叉验证 → 行业适配 → 多方法估值 → 消极/中性/积极三情景 → 可视化报告 → 下次增量跟踪**。用户要求估值时，必须明确显示最近股价/市值、各方法合理股权市值、三情景合理市值和每股价格、相对市价空间、核心驱动与置信度。缺乏合理数据时，用“无法可靠估值 / null”和待验证条件代替虚构数值。

**禁止把安装 Skill 等同于已拥有行情/官网检索/常驻监控。** 使用宿主可用的联网浏览或数据 API 实际检索；使用脚本只做数值计算；需要持续扫描应由宿主调度器/自动化任务驱动。

## 必须执行的研究步骤
1. **标的确认。** 识别代码、交易所、公司、是否 ST/*ST/退市风险、行业/主营占比，列报告 `as_of`、行情 `price_date`、财报披露日，任何差异必须标出；不猜股票代码或市场数据。
2. **最重要：来源登记与交叉核验。** 优先公司/交易所正式披露，其次政策发布机关、统计和行业机构，之后结构化金融数据库、独立原创研究和媒体。每个关键数字/重大事件创建 claim_id、原始链接、原始出处与发布日期、数据口径、报告期；重新刊载者共享 `origin_id`，不算新的独立证据。**详情首先读 `references/evidence-verification.md`。** 有条件执行 `scripts/check_evidence.py`，但该脚本只能离线核验元数据，**需要实际浏览原文才能称事实核实**。
3. **财报完整性。** 近 3–5 年和最近 4 个单季度：归母与扣非、营收/毛利/净利、CFO、capex、应收与存货、负债/净现金、费用率、股本/增发/审计、更正公告；TTM = 最近 4 个单季度，不能累加四份年初至今累计值。财务数据应匹配官方报告页码并保留追溯链。
4. **行业与竞品。** 以真实商业模式而非仅行业代码选 3–7 家同行；对比收入增长、ROE、毛利率、FCF、利润质量、PE/PB/EV倍数、行业驱动、产能/价格、需求和份额；监控龙头的经营恶化可能意味着行业压力也可能意味着标的份额提升，按传导逻辑判断。
5. **政策及新闻。** 实施日期、发文机关、正式/征求意见、适用区域/税号/子行业必须确认。没有原始文件的“政策利好”一律待核实；多条媒体重复不等于多源独立证据。
6. **多种方法估值、不能套固定倍数。** 按 `references/valuation-playbooks.md`：盈利消费/制造 PE + DCF + EV/EBITDA；资产型 PB + DCF；分部不同的 SOTP；银行/保险/券商必须行业专属 PB-ROE/剩余收益/EV等，不能使用工业公司 DCF。倍数参照可比公司 P25/median/P75、标的历史区间、周期和基本面；模型可用时至少两种方法并列展示分项、分歧及采用权重。**不要用同一输入驱动的多个方法冒充独立证据。**
7. **三情景必须分别交代驱动。** 消极(bear)/中性(base)/积极(bull)各自列收入、利润率、利润/FCF、合理 PE/EV倍数或 WACC、债务/稀释、估值方法及假设来源，并计算**整体合理股权市值（亿元）+ 合理每股价格（元）+ 相对现价变化%**。如负净资产、连续亏损、退市、债务重整条件不成立，则以条件推演或 null 明示；绝不能强造三数。比较每种方法差异、敏感性、隐含增长假设。
8. **变化与监控。** 将本次与先前同口径报告比较：经营变化、行业竞争、政策事件、债务及治理、估值假设变化、单纯价格变化，不能混淆；保留快照、引用链、风险触发条件；使用 `references/monitoring.md`。
9. **输出报告。** 开头给核心结论及合理估值与可信度，然后财务趋势（收入/利润/现金流）、同行对照、三情景多模型对比、政策与风险、投资逻辑反证、哪些信息尚需核验、原始来源页码/链接和更新时间。详情 `references/report-template.md`。明确标注：事实 / 推断 / 模型假设 / 谣言。
10. **跨模型运行。** 指令格式通用 `SKILL.md`。Kimi Code CLI 可直接加载；DeepSeek 等若在支持自定义 Skill 的 Agent 中可直接读取。普通 DeepSeek/Kimi 聊天网页不能当然安装并自动运行全部脚本。若需要 API 生成文本，用 `references/model-providers.md` 的 `llm_research_assist.py`；LLM 仅写草稿，财报和数学仍由可信数据及程序决定。

## 脚本（只依赖 Python 3.10+ 标准库）
```bash
python scripts/check_evidence.py --input examples/evidence-demo.json --output outputs/evidence-check.json
python scripts/run_analysis.py --input examples/demo-company.json --outdir outputs/demo
python scripts/compare_snapshots.py --old examples/demo-company.json --new examples/demo-company.json --output outputs/delta.json
python scripts/llm_research_assist.py --provider deepseek --valuation outputs/demo/valuation.json --evidence outputs/evidence-check.json --output outputs/draft.md --dry-run
python -m unittest discover -s tests -v
```
本包演示数据为**完全虚构**。`check_evidence.py` 不联网且输入来源标签可被伪造：metadata_corroborated ≠ 实质验证成功；任何报告必须人工或通过宿主浏览工具打开原文。不要上传 API 密钥、商业机密、客户隐私或未公开重大信息。若没有运行环境，按上述规则人工研究并披露限制。
