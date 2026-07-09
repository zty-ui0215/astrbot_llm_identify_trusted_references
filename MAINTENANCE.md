# LLM Identify Trusted References 云端仓库维护说明

本文说明 `https://github.com/zty-ui0215/llm-identify-trusted-references` 的维护方式。该仓库用于接收、审查、归档来自官方 API 端点的志愿模型指纹候选数据。

## 仓库定位

该仓库不是实时数据库，也不是自动信任源。它的职责是：

- 接收插件生成的脱敏候选包。
- 验证候选包是否来自官方 API 端点。
- 审查候选包是否符合隐私和 schema 要求。
- 将通过维护者审核的数据整理为可信参考样本。
- 为插件后续版本、内置语料、公共指纹源提供可追溯参考。

候选数据默认状态是 `maintainer_review_required`。只有经过人工审查和一致性检查后，才能进入 `data/accepted/`。

## 推荐目录结构

```text
.github/
  ISSUE_TEMPLATE/
    trusted-reference-candidate.yml
  workflows/
    validate.yml
data/
  candidates/
    <provider>/<model>/<hash-or-date>.json
  accepted/
    <provider>/<model>/<version>.json
schemas/
  trusted-reference-candidate.schema.json
scripts/
  validate_candidate.py
docs/
  privacy.md
README.md
CONTRIBUTING.md
```

## 数据流

1. 用户在插件 page 中对官方 API 执行完整直连检测。
2. 插件识别官方端点，例如 `api.openai.com/v1` 或 `dashscope.aliyuncs.com/compatible-mode/v1`。
3. 插件生成脱敏候选包，不包含 raw prompt、raw completion、API Key、headers、账号标识、IP、私有 URL。
4. 用户点击“一键上报”，进入预填 GitHub Issue 页面。
5. 维护者检查 issue 中的 JSON 包。
6. 维护者可要求补充多次检测结果，或将候选包转为 PR 放入 `data/candidates/`。
7. 通过审查后，将记录归档到 `data/accepted/`。

## 官方端点判断

只接受官方平台 API。常见可接受示例：

- OpenAI: `https://api.openai.com/v1`
- Anthropic: `https://api.anthropic.com`
- Google Gemini: `https://generativelanguage.googleapis.com/v1beta`
- 阿里云百炼 / DashScope OpenAI 兼容接口: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Mistral: `https://api.mistral.ai/v1`
- Cohere: `https://api.cohere.com`
- DeepSeek: `https://api.deepseek.com`
- 火山方舟: `https://ark.cn-beijing.volces.com/api/v3`
- 智谱: `https://open.bigmodel.cn/api/paas/v4`
- Moonshot: `https://api.moonshot.cn/v1`

拒绝以下来源：

- 代理、镜像、反代、网关、聚合平台。
- 非 HTTPS 端点。
- 域名伪装，例如 `api.openai.com.proxy.example`。
- 无法证明为官方平台的 OpenAI-compatible 服务。

## 审核标准

维护者审核候选包时至少检查：

- `schema_version` 是否为 `trusted-reference-candidate/v1`。
- `endpoint.official_host` 是否在官方端点列表中。
- `endpoint.provider` 与 host 是否匹配。
- `model.claimed_by_official_endpoint` 是否合理。
- `probe_ids` 是否来自当前插件探针集。
- `scores`、`capability_scores`、`fingerprint_vector` 是否完整。
- 是否存在敏感信息。
- 多次提交之间是否稳定，是否存在异常漂移。

建议至少两次独立检测结果一致后再进入 `accepted`。

## 隐私规则

仓库不得保存：

- API Key、Bearer token、cookie、authorization header。
- raw prompt、raw completion、真实用户聊天内容。
- 账号 ID、IP 地址、请求 ID 中可识别用户的信息。
- 私有 base URL、账单截图、控制台截图。
- 包含商业秘密或个人信息的任何字段。

如发现敏感信息，应立即：

1. 关闭 issue 或 PR。
2. 删除敏感提交，必要时重写 Git 历史。
3. 提醒提交者重新通过插件导出脱敏包。
4. 如 GitHub 页面已经暴露密钥，提醒提交者立即轮换密钥。

## Issue 处理流程

建议标签：

- `trusted-reference-candidate`
- `needs-review`
- `needs-more-runs`
- `privacy-risk`
- `accepted`
- `rejected`

处理步骤：

1. 确认 issue 来自模板。
2. 复制 JSON 到本地临时文件。
3. 运行验证脚本：

```bash
python scripts/validate_candidate.py path/to/candidate.json
```

4. 检查端点、模型名、分数、探针覆盖。
5. 如缺少多次检测证据，打 `needs-more-runs`。
6. 如可接受，创建 PR 放入 `data/candidates/` 或直接归档到 `data/accepted/`。
7. 在 issue 中说明处理结论并关闭。

## PR 处理流程

1. 确认 GitHub Actions `Validate candidates` 通过。
2. 检查文件路径是否符合：

```text
data/candidates/<provider>/<model>/<hash-or-date>.json
```

3. 人工审查 JSON 内容和隐私风险。
4. 对重复数据进行去重。
5. 合并后定期从 `candidates` 归档到 `accepted`。

## accepted 数据维护

`data/accepted/` 中的数据应满足：

- 已通过 schema 校验。
- 已确认官方端点。
- 无敏感信息。
- 至少一次人工审核，推荐多次独立检测交叉确认。
- 记录来源 issue 或 PR 编号。

建议为 accepted 记录增加维护者字段，例如：

```json
{
  "review": {
    "status": "accepted",
    "reviewer": "maintainer-handle",
    "source_issue": 12,
    "accepted_at": "2026-07-09",
    "notes": "Consistent with two official endpoint runs."
  }
}
```

## 发布节奏

推荐每 2-4 周整理一次：

1. 汇总 accepted 数据。
2. 检查是否有模型退役、模型别名变化、官方文档更新。
3. 生成 release，例如 `trusted-corpus-2026.07`。
4. 在 release notes 中列出新增 provider、model、记录数量和重要变更。
5. 插件侧可在后续版本中同步这些记录到内置语料或公共源。

## 质量控制

维护时应避免让单次结果过度影响指纹库。建议：

- 同一模型保留多个时间桶的记录。
- 标记模型热更新或别名变化。
- 对高漂移模型保留 `drift_notes`。
- 不把辅助 LLM 判断作为唯一证据。
- 优先使用协议、token、side-channel、探针统计等可复验特征。

## 安全建议

- 默认不开放自动写入 accepted。
- 不使用 GitHub Actions 自动接受 issue 数据。
- 不在 CI 日志输出完整候选包之外的额外请求信息。
- 对 fork PR 保持最小权限。
- 若引入自动同步脚本，必须先进入 `data/candidates/`，再人工审核。

## 本地维护命令

```bash
# 校验候选数据
python scripts/validate_candidate.py data/candidates

# 查看未提交变更
git status

# 创建维护分支
git checkout -b review/candidate-<provider>-<model>

# 提交审核后的候选数据
git add data/candidates schemas scripts docs
git commit -m "Add trusted reference candidate for <provider> <model>"

# 推送到云端仓库
git push origin review/candidate-<provider>-<model>
```

## 与插件的关系

插件负责：

- 检测官方 API。
- 生成脱敏候选包。
- 提供一键上报入口。
- 在本地保留备份导出。

云端仓库负责：

- 接收候选包。
- 审核隐私和真实性。
- 维护可信参考数据。
- 为后续插件更新提供可追溯数据源。

两者之间不应有静默自动上传。用户必须主动点击上报，维护者必须主动审核。
