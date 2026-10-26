# 永创智能（603901.SH）案例

数据截止：2026-10-26。案例用于展示 `china-stock-valuation` v1.1 的证据登记、行业适配、多模型估值和三情景输出。

## 文件

- [`executive-research.md`](executive-research.md)：中文研究结论、假设和风险。
- [`input.json`](input.json)：估值、同行、财务趋势和情景输入。
- [`evidence.json`](evidence.json)：重点事实的证据登记表。
- [`evidence-audit.json`](evidence-audit.json)：离线元数据核验结果。
- [`report/valuation.json`](report/valuation.json)：可复算的模型输出。
- [`report/report.html`](report/report.html)：自包含可视化报告，另含人工整理的研究摘要。

## 复算

从仓库根目录执行：

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

预期证据审计摘要为：5 条重点 claim，3 条元数据通过交叉检查，2 条仍需复核。复算得到的 `valuation.json` 应与仓库版本一致。

`report/report.html` 比脚本当前的纯生成版本多一段人工研究摘要，并保留原始生成时间，所以 HTML 不应按文件哈希比较；估值数值以 `valuation.json` 为可复算基准。

## 结论边界

中性情景约 60–65 亿元、每股约 10–11.3 元，是基于 2027 年经营假设的条件估值。积极情景需要利润和机器人业务商业化明显超出基准预期；消极情景反映订单、利润率和现金流不及预期的下行风险。三情景不是概率分布，也不是买卖建议。
