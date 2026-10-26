# 数据来源、核验流程与数据契约

## 可信度优先级（不是简单的排名）

1. 法定/官方披露：巨潮资讯 https://www.cninfo.com.cn/；上交所 https://www.sse.com.cn/；深交所 https://www.szse.cn/；北交所 https://www.bse.cn/disclosure/announcement.html；公司 IR；审计报告。关注：年报、半年报、季报、业绩预告/快报、重大合同、问询函回复、回购及减持、实控人/股权变动、诉讼、处罚、重大资产重组。官方披露内容本身也可能有误，应留意更正和审计意见。
2. 宏观/行业官方：国家统计局 https://data.stats.gov.cn/；工信部 https://www.miit.gov.cn/gxsj/index.html；中国政府网政策库 https://sousuo.www.gov.cn/zcwjk/；央行、金融监管总局、证监会、发改委、财政部、生态环境部、海关总署、各地政府相关原文。行业组织需检查统计口径和样本。
3. 批量金融数据：Tushare Pro https://tushare.pro/document/1?doc_id=108；AKShare https://akshare.akfamily.xyz/；BaoStock https://github.com/zxygithub/baostock；授权商业数据 Wind/Choice/iFinD。注意二次加工、可用性、服务条款/授权、积分/频率限制。
4. 公司经营/用户/产品数据：公司月度快报、IR 业绩会、产销快报、经营简报、监管及行业协会、其他上市竞品正式披露；电商平台/应用商店/第三方移动数据仅作近似线索，不能视为审计数据。没有可靠来源则写“未披露/无法核实”。
5. 资讯/市场舆论：用于发现线索而非确认事实；政策只以原始法规文件、部门通告为准。

## 下载/解析阶段
- 报告期和发布日期分开存储，保存 `retrieved_at`、`source_url`、标题、原文哈希、报告版本及更正记录；对指标保留源文数字与页码（能获得时）。
- 将财务单位统一为人民币亿元，留原币/汇率。净利润同时标记 `net_profit_total` 和 `net_income_parent`，不得混合；核查归母净资产和少数股东权益。
- 核查：资产=负债+权益，经营/投资/筹资现金流与现金变动勾稽，期初+当期变动≈期末（含汇率差异）；利润与扣非差别；两次来源差异及更正。
- 重要：A 股半年报、三季报现金流量表和利润表常是年初至报告期末累计值；算单季度用差分，Q4=全年-Q3累计。Q1 是单季。不能简单把四份累计报表相加。
- 遇到合并范围变更、资产注入、会计政策调整、业务出售、海外汇率、一次性收入、增发回购，应标明“不可比”，必要时重构同口径历史。
- 日线行情注意停牌、除权除息、成交时区、成份股历史变更、退市幸存者偏差。以收盘日的总股本和价格估算总市值，注意限售股、市值与流通市值不同。

## 推荐数据表

`companies`: ticker, exchange, company_name, industry, subindustry, security_type.

`financial_facts`: ticker, metric, value, unit, period_start, period_end, period_type, public_at, is_ytd, consolidated, audited, version, source_url, source_hash, recorded_at.

`market`: ticker, trade_date, price_type, close, shares_100m, market_cap_100m, adj_flag, vendor, retrieved_at.

`operating_kpis`: ticker, metric, value, unit, period, source_url, method, confidence, coverage_note.

`policy_events`: title, agency, issued_at, effective_at, region, stage, source_url, affected_industries, causal_mechanism, confidence.

`research_versions`: ticker, run_at, model_version, historical_data_cutoff, thesis, core_assumptions, fair_value_low/base/high, probability_notes, alerts.

## 缺失与冲突规则
- 无官方经营 KPI 时：不要伪造活跃用户、订单、ASP、市场份额。使用公开代理指标并说明采样偏差。
- 第三方数据与官方财报不一致：优先以最新官方更正公告核准，保留冲突日志；不要自动取均值。
- 记录成功但样本旧于合理窗口、URL 不可访问、付费墙、API 拒绝、字段含义变化，都视为缺失，不可默默用缓存替代“最新”。

## 当前公开接口核验（2026-10）
- Tushare 财务表 `income`、`balancesheet`、`cashflow`、`fina_indicator` 等存在相应权限及积分要求；`daily_basic` 为交易日估值指标，不能和未复权价混为历史总回报。
- AKShare 接口随源网站变动可能失效；BaoStock 免费易入门，但财务和行业数据覆盖及新鲜度需自行核验。
- 交易所公开网页不等于稳定、无鉴权、可商业再分发的 API，签约或授权前不能做商业稳定性承诺。
