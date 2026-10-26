# 中国股票估值与基本面监控 Skill v1.1

**适用**：中国 A 股公司财报分析、竞品与政策研究、来源多方验证、多方法价值区间、悲观/中性/乐观三情景及后续变化监控。模型规范与计算脚本分离，可供 Codex、Claude Code、Kimi Code CLI 等支持 Agent Skills 的宿主使用；DeepSeek 等可经支持读取 Skill 的 Agent 或官方 API（只做生成报告草稿）接入。

## 相比 v1.0 的升级

| 能力 | v1.1 实现 | 未实现的部分 |
|---|---|---|
| 多源校验 | 建立 claim ledger、原始来源 `origin_id` 去重、主来源门槛、数字冲突/单位/期间检测、严格模式阻断 | 不会主动联网打开每个公告链接核实内容，必须依靠宿主搜索或人工逐项确认 |
| 三情景 | 分别设置利润、EBITDA、FCFF、净债务、股本、折现率、增长、估值倍数，计算三情景合理市值/每股价值 | 不自动预测真实经营数据，需来自研报/财报/可核对的模型假设 |
| 多模型 | PE、PB、EV/EBITDA、DCF、SOTP，显示各方法结果与权重 | 银行 PB-ROE/保险精算 EV/创新药 rNPV 未实现可执行的行业模型；规则文档说明行业例外 |
| 国内模型 | 可选 DeepSeek、Kimi 国际与中国大陆官方 OpenAI-compatible API；Kimi Code CLI 原生 Skill | 未实际支付调用测试；API 费用、账户可用模型需用户自行确认；普通聊天网页不一定可上传 Skill |
| 可视化 | HTML 自包含报告、负数图表、证据核验状态、三情景价位和驱动 | 实时股价、自动爬取财报、消息推送、定时器需要独立基础设施 |

## 文件夹内容

```text
china-stock-valuation-skill-v1.1/
├── SKILL.md                           主研究流程与 Agent 调用条件
├── README.md                          当前说明
├── CHANGELOG.md                       修改日志
├── references/
│   ├── evidence-verification.md        交叉核验与反媒体转载规则
│   ├── valuation-playbooks.md          估值方法及行业限制
│   ├── model-providers.md              Kimi / DeepSeek 使用
│   ├── data-sources.md                 A股数据源
│   ├── sector-metrics.md               行业指标
│   ├── monitoring.md                   变化监控
│   └── report-template.md              研究报告框架
├── scripts/
│   ├── check_evidence.py               离线信息来源元数据核验
│   ├── run_analysis.py                 5模型/3情景计算与HTML报告
│   ├── compare_snapshots.py            差异检测
│   ├── llm_research_assist.py          国内模型可选API草稿生成
│   ├── fetch_financial_optional.py     第三方财务抓取（未经官方核验）
│   └── fetch_optional.py               第三方行情抓取（未经官方核验）
├── examples/
│   ├── demo-company.json               100%虚构、仅用于测试
│   └── evidence-demo.json              100%虚构、仅用于测试
├── outputs/demo/                      生成的示范HTML和JSON
└── tests/                             自动测试
```

## 快速试用：无需任何 API Key

Python 3.10+ 可直接运行，基础功能只使用标准库。

```bash
cd china-stock-valuation-skill-v1.1
python scripts/check_evidence.py --input examples/evidence-demo.json --output outputs/evidence-check.json
python scripts/run_analysis.py --input examples/demo-company.json --evidence examples/evidence-demo.json --outdir outputs/demo
python -m unittest discover -s tests -v
```

打开 `outputs/demo/report.html`，可见三情景估值与来源核验状态。严格来源门槛：

```bash
python scripts/run_analysis.py --input examples/demo-company.json --evidence examples/evidence-demo.json --strict-evidence --outdir outputs/strict-demo
```

因为演示账本特意有一条同源转载传闻，所以这条命令**预期拒绝**，说明阻断机制生效；替换为真实且核对的证据清单才能通过。**通过“元数据门槛”也不代表程序读过官网原文。**

## 两个国内模型接口（可选，调用可能收费）

### DeepSeek

```bash
# 查看配置，绝不联网
python scripts/llm_research_assist.py --provider deepseek --valuation outputs/demo/valuation.json --evidence outputs/evidence-check.json --output outputs/demo/deepseek.md --dry-run

# 确认数据内容可发送至模型服务商后，按需自行执行
export DEEPSEEK_API_KEY="<API_KEY>"
python scripts/llm_research_assist.py --provider deepseek --model deepseek-flash --valuation outputs/demo/valuation.json --evidence outputs/evidence-check.json --output outputs/demo/deepseek.md
```

### Kimi / Moonshot

```bash
export MOONSHOT_API_KEY="<API_KEY>"
# 中国大陆地区 API；将 MODEL_NAME 换成 Moonshot 平台当前可用模型ID
python scripts/llm_research_assist.py --provider kimi-cn --model MODEL_NAME --valuation outputs/demo/valuation.json --evidence outputs/evidence-check.json --output outputs/demo/kimi.md
```

Kimi 国际平台使用 `--provider kimi`。两种模型只负责基于传入资料**生成研究草稿**，不具备自动查找事实、下载公告或复核估值输入的能力。用户不能通过 API 调用绕过来源核验。

## 安装兼容 Agent

- Codex：复制文件夹内容到 `<project>/.agents/skills/china-stock-valuation/`。
- Claude Code：复制到 `<project>/.claude/skills/china-stock-valuation/`。
- Kimi Code CLI：复制到 `<project>/.kimi-code/skills/china-stock-valuation/` 或 `<project>/.agents/skills/china-stock-valuation/`，并可用 `/skill:china-stock-valuation` 启用。
- VS Code Agent：复制到 `<project>/.github/skills/china-stock-valuation/` 或 `.agents/skills/`。
- DeepSeek、Kimi 普通网页：能否上传/执行 Skill 取决于网页产品/账户能力。可复制 `SKILL.md` 和必要的 `references/` 为工作指令；使用本地或服务端 Python 调用 DeepSeek/Kimi API 只生成草稿。
- 用 OpenClaw、其他 Agents：请按照相应宿主的当前 skills 搜索路径复制整个文件夹；不要假设不同宿主自动具有 Python、联网、浏览器及调度能力。

## 研究实战关键提醒

1. `examples` 下任何数字都不存在真实公司，不能当作市场参考参数。
2. `run_analysis.py` 的合理估值是**给定输入及模型设定下的条件结果**，不自动定义某行业的合理 PE。
3. 原始数据优先交易所披露；不要将三个同源媒体复制当成三个独立证据，也不要让三种 LLM 重复同一虚假数据后认为“交叉验证”。
4. 财报来源失效、净资产为负/债务重整缺乏明确条款、极高股权稀释风险时允许输出 `null`，并显示需要验证的前置条件。
5. 商业化应考虑行情许可、研究报告版权、交易所数据接口使用条件、提示词注入、数据隐私、模型服务商费用与合规要求。

模型接口官方资料：DeepSeek https://api-docs.deepseek.com/zh-cn/，Kimi Code Skills https://moonshotai.github.io/kimi-code/zh/customization/skills，Agent Skills https://agentskills.io/。
