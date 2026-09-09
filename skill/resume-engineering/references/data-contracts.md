# 数据契约 v1

结构化JSON为规范事实，Markdown为可读解释；两者不各自维护冲突真相。未来Excel作为导入/导出视图，回写须显示差异并执行合并规则。

## Fact

使用 [fact.schema.json](../assets/schemas/fact.schema.json)。所有基础字段显式出现；未知文本用null、集合用空数组，不补猜值。category支持education、research、work、project、capability、award、publication、patent、other。

title是条目标题；role是真实历史Title或明确项目角色。contribution_scope保留个人与团队边界。responsibility、technical_approach、method、tools、result均来自来源，不从岗位JD反向补造。

metric以原始字符串value保留“约”“区间”等语义，unit、context、source_ref必填。无单位的事实可以保存在待确认条目，不能作为已验证指标进入输出。日期ISO完整值或YYYY-MM，precision跟随来源；不为了补齐日期改毕业月份。

status: draft → pending_review → verified；冲突置conflicted，废弃置retired。verified需至少一个支持性证据，用户明确确认也是一种证据；不代表已独立第三方核实。confidence表示证据置信程度，不能代替审核状态。

## Evidence

嵌入事实的evidence索引含 evidence_id、kind、locator、supports、review_status。kind包括user_confirmation、document、public_reference、measurement。locator使用私人工作目录相对位置/记录ID；禁止包含密码、带Token的URL。原文件留private目录，公开输出只使用获准改写后的事实，不自动携带证据路径。

## 补充与合并

1. 以fact_id定位；无ID时依据时间、机构/背景、项目和角色找候选重复项。
2. 比较字段，不以措辞差异自动新增事实。
3. 支持性补充追加到同一事实，版本递增；既有证据不丢失。
4. 冲突建立记录：conflict_id、fact_ids、field、candidate_values、source_refs、status、resolution。冲突未解决不生成确定表述。
5. 更改Title、时间、量化结果或贡献范围时记录确认依据；引用旧版本的用途批准失效。

## 中英文词汇

字段：term_id、zh、en、abbreviation、definition、context、source_refs、related_fact_ids、review_status。词汇表可以解释未掌握的方法；只有verified能力事实才支持“会使用”的声明。词汇变化只影响引用该词的产物。

## 照片/素材

字段：asset_id、version、kind(original/derived/virtual)、source_asset_id、private_locator、rights_holder、consent_record、allowed_uses、metadata_review、transformation_record。
原图不覆盖；授权衍生图保持身份特征。virtual标明虚拟，不能冒充真实工作现场。没有照片授权则使用不含身份的占位结构或省略照片。

## 授权证据

approval记录review_id、reviewed_at、fact_version、evidence_ref；拒绝或撤回必须说明原因。每次输出把fact_id/version、词汇版本、模板版本记录到依赖图，便于追溯。
