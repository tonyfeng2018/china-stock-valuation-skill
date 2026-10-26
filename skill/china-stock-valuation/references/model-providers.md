# 模型无关运行机制与国内模型支持

## 三层架构（重要）
1. Skill 层：`SKILL.md` + `references/`，是 Agent 的研究操作规范，模型本身只需能理解中文与阅读文件。
2. Tool 层：Python 模型计算 / provenance 离线核验 / HTML 输出，可在支持 shell/python 的 Agent 中运行；普通网页版聊天如果无执行环境，只能手工按规范输出。
3. LLM 文本层：`scripts/llm_research_assist.py` 可选通过 OpenAI-compatible Chat Completions API 调用 DeepSeek、Kimi，对**已经计算好的**结果写带依据的研究草稿。LLM 不负责数学模型，也不自动联网抓取；模型调用成功不代表事实被验证。

## API 支持 / 环境变量
- DeepSeek：`https://api.deepseek.com`；`DEEPSEEK_API_KEY`；默认 `deepseek-flash`，也可 `--model` 指定官方当时支持的其它型号。
- Kimi 国际平台：`https://api.moonshot.ai/v1`；`MOONSHOT_API_KEY`；**显式 `--model`**，避免旧模型名过期。中国大陆平台：`--provider kimi-cn` 使用 `https://api.moonshot.cn/v1`。
- 只向白名单官方 HTTPS 域名发请求，不支持未审核的代理 endpoint，避免 API key 泄漏。API 按各服务商规则可能收费；未持有密钥亦可运行估值和证据检查。
- 如果通过 Kimi Code CLI 本身运行 Skill，直接读取 `SKILL.md`，无需再调用 Kimi API；如果通过 DeepSeek 驱动的其他 Agent 读取 Skill，同理。但不代表 DeepSeek 官网普通聊天支持一键安装 Skill。

## 使用示例
```bash
# 未联网演练，无需密钥：
python scripts/llm_research_assist.py --provider deepseek --valuation outputs/demo/valuation.json --evidence outputs/evidence-check.json --output outputs/demo/draft.md --dry-run

# 自愿使用外部 API（每次调用会上传所指定文件的内容到相应服务商）：
export DEEPSEEK_API_KEY="..."   # 不要提交到 Git 或贴入聊天
python scripts/llm_research_assist.py --provider deepseek --model deepseek-flash --valuation outputs/demo/valuation.json --evidence outputs/evidence-check.json --output outputs/demo/draft.md

export MOONSHOT_API_KEY="..."
python scripts/llm_research_assist.py --provider kimi-cn --model "请填入控制台当前可用的模型 ID" --valuation outputs/demo/valuation.json --evidence outputs/evidence-check.json --output outputs/demo/draft-kimi.md
```

服务商官方参考：DeepSeek https://api-docs.deepseek.com/zh-cn/ ；Kimi Code Skills https://moonshotai.github.io/kimi-code/zh/customization/skills 。实际可用模型名、API 价格、上下文长度会变化，以平台控制台为准。
