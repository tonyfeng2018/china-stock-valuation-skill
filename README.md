# 中国股票研究与估值 Skill

一个面向中国 A 股的可复核研究与估值工作流。它把公开证据登记、来源交叉核验、行业适配、多模型估值、消极/中性/积极三情景和增量跟踪拆成可执行步骤，并附带 Python 计算与检查脚本。

当前公开版本：**v1.1**（整理日期：2026-10-26）。

> 本仓库用于研究流程演示与面试交流，不构成投资建议。案例中的目标价是给定假设下的条件结果，不是收益承诺或交易指令。

## 仓库内容

```text
.
├── skill/china-stock-valuation/          可安装的 Agent Skill
├── case-studies/
│   └── 603901.SH-yongchuang-intelligent/ 永创智能案例
├── INTERVIEW_GUIDE.md                    面试讲解提纲
└── SECURITY.md                           密钥与数据安全说明
```

## 核心能力

- 关键事实建立 claim ledger，并按原始出处 `origin_id` 去重；媒体转载不冒充独立证据。
- 根据商业模式选择估值方法，避免对所有公司机械套用 PE 或 DCF。
- 计算 PE、PB、EV/EBITDA、简化 DCF 和 SOTP，并说明不适用的方法。
- 输出消极、中性、积极三种情景的合理市值、每股价值、相对现价空间和驱动假设。
- 支持 DeepSeek/Kimi API 生成受输入约束的中文研究草稿；LLM 不负责验证事实或计算估值。
- 保存研究快照并比较变化，区分基本面变化、模型参数变化与单纯价格变化。

## 30 秒运行

基础估值、证据检查和测试只需要 Python 3.10+，不需要 API Key。

```bash
git clone https://github.com/tonyfeng2018/china-stock-valuation-skill.git
cd china-stock-valuation/skill/china-stock-valuation

python3 scripts/check_evidence.py \
  --input examples/evidence-demo.json \
  --output outputs/evidence-check.json

python3 scripts/run_analysis.py \
  --input examples/demo-company.json \
  --evidence examples/evidence-demo.json \
  --outdir outputs/demo

python3 -m unittest discover -s tests -v
```

然后打开 `outputs/demo/report.html`。示范公司和数字完全虚构，仅用于测试。

## 安装为 Skill

将 `skill/china-stock-valuation/` 整个目录复制到宿主支持的 Skill 路径：

| 宿主 | 项目级路径 | 调用方式 |
|---|---|---|
| Codex / 通用 Agent Skills | `.agents/skills/china-stock-valuation/` | 直接提问，或显式要求使用 `china-stock-valuation` |
| Claude Code | `.claude/skills/china-stock-valuation/` | 直接提问或显式指定 Skill |
| Kimi Code CLI | `.kimi-code/skills/china-stock-valuation/` 或 `.agents/skills/china-stock-valuation/` | `/skill:china-stock-valuation 评估 603901.SH` |
| VS Code Agent | `.github/skills/china-stock-valuation/` 或 `.agents/skills/` | 由宿主发现并加载 |

Kimi Code CLI 的当前官方文档也支持用户级 `$KIMI_CODE_HOME/skills/`（默认 `~/.kimi-code/skills/`）及 `~/.agents/skills/`。不同宿主是否具备联网、Python、浏览器和定时器能力需要单独确认；安装 Skill 不等于自动获得实时行情或公告数据。

## 使用示例

安装后可直接提出可验证任务：

```text
使用 china-stock-valuation 评估 603901.SH。
数据截止到 2026-10-26；先核对交易所/公司公告，再用同行和历史区间校准参数。
输出消极、中性、积极三情景，并明确哪些事实未完成交叉验证。
```

对真实标的，推荐顺序是：

1. 确认代码、交易所、报告和行情时间点。
2. 登记关键事实及原始来源，运行 `check_evidence.py` 检查元数据冲突。
3. 根据商业模式选择模型与同行，填写研究输入 JSON。
4. 运行 `run_analysis.py`，审阅各模型差异和假设敏感性。
5. 人工打开原始公告逐项复核；元数据通过不等于事实已核实。

## 永创智能案例

[永创智能（603901.SH）案例](case-studies/603901.SH-yongchuang-intelligent/executive-research.md)展示了完整流程：

- 包装自动化主业与机器人新业务分开估值。
- 用 PE、PB、EV/EBITDA、简化 DCF 交叉检查三情景。
- 明确把“量产销售条件”与“已规模化盈利”分开。
- 将媒体涨停归因和机构预测标为第三方观点，不视为已实现业绩。
- 记录股本变化、库存、合同负债与现金流风险。

复算案例：

```bash
cd skill/china-stock-valuation
python3 scripts/check_evidence.py \
  --input ../../case-studies/603901.SH-yongchuang-intelligent/evidence.json \
  --output ../../case-studies/603901.SH-yongchuang-intelligent/evidence-audit.reproduced.json

python3 scripts/run_analysis.py \
  --input ../../case-studies/603901.SH-yongchuang-intelligent/input.json \
  --evidence ../../case-studies/603901.SH-yongchuang-intelligent/evidence.json \
  --outdir ../../case-studies/603901.SH-yongchuang-intelligent/report-reproduced
```

复算得到的 `valuation.json` 应与案例中的版本一致。仓库内 `report/report.html` 另含为面试展示整理的人工研究摘要，因此 HTML 文件不会逐字节一致；模型数值仍来自同一输入和脚本。

## DeepSeek / Kimi（可选）

API 只用于把已经计算好的估值与证据审计结果整理成草稿，调用会把所指定文件内容发送给对应服务商。

```bash
# 不联网演练
python3 scripts/llm_research_assist.py \
  --provider deepseek \
  --valuation outputs/demo/valuation.json \
  --evidence outputs/evidence-check.json \
  --output outputs/demo/draft.md \
  --dry-run

# 真正调用前，由使用者在自己的终端设置环境变量
export DEEPSEEK_API_KEY="<YOUR_KEY>"
python3 scripts/llm_research_assist.py \
  --provider deepseek \
  --model deepseek-flash \
  --valuation outputs/demo/valuation.json \
  --evidence outputs/evidence-check.json \
  --output outputs/demo/draft.md
```

Kimi 使用 `MOONSHOT_API_KEY`，并要求用 `--model` 填写控制台当前可用模型 ID。不要把密钥写入 JSON、脚本、README、Git 历史或聊天记录。

## 已知边界

- 脚本不会自动验证网页、公告或新闻内容，证据元数据也可能被错误填写。
- 行业专用的银行 PB-ROE、保险内含价值、创新药 rNPV、资源 NAV 计算器尚未完整实现。
- 估值引擎不会自动预测真实业绩，也不会自动确定合理倍数。
- 案例使用 2026-10-26 当时可见的公开数据快照；后续财报和价格变化不会自动回填。
- 公开数据源可能有版权、许可、频率及再分发限制，商业化前必须另行确认。

详细规则见 [`SKILL.md`](skill/china-stock-valuation/SKILL.md)。
