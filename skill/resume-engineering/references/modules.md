# 模块契约

修改范围以使用者工作目录为根。私人输入不得写回公开Skill。模块表定义职责，不要求一次加载所有模块内容。

| 模块 | 输入 | 输出/允许写入 | 依赖 | 验收 |
|---|---|---|---|---|
| planning | 用户目标、已有项目状态 | project计划/状态/决策 | 无 | 范围、用途、工具、缺口明确 |
| facts | 原始教育/工作/项目资料与确认 | facts事实、private证据索引 | planning | 无无源指标；冲突记录；真实Title |
| glossary | 术语来源、行业语境 | facts词汇 | facts可选 | 中英文、缩写、语境明确；非技能声明 |
| media | 本人原图、素材授权、用途 | private原图索引、授权衍生素材 | privacy | 身份特征、授权、EXIF检查 |
| privacy | 事实版本、用途、授权 | 用途批准、撤回记录、approved投影 | facts/media | 默认拒绝、逐用途审核 |
| website | public_website投影、视觉资源 | website | privacy/media | 响应式、链接、公开包 |
| assistant | public_ai投影、运行环境 | assistant | privacy | 真实浏览器问答、引用和来源拒绝检查 |
| resume | targeted_resume投影、岗位策略 | resumes、exports | privacy/media/glossary | 事实一致、岗位排序、两页可读 |
| release | 产物、目标环境、授权 | reports、发布清单、限定目标 | 相应产物 | 备份、哈希、线上验证 |
| retrospective | 验收和决策记录 | reports复盘、project维护状态 | 本轮已完成项 | 区分已验证与待办 |

## 变化分类

- 只改简历项目顺序：resume + 验收记录；不加载AI或网站代码。
- 补充事实：facts → privacy → 依赖图中下游标为stale；仅在授权范围更新输出。
- 只换照片：media → 使用该照片的模板实例；事实不变。
- 收回公开授权：privacy → 下游全部隔离/撤回待办；不能继续发布旧产物。
- 修改共享视觉模板：所有引用该模板版本的产物需重新排版验收，不需要重写事实。
- 修改AI地址：assistant/release，验证浏览器Origin与回答；不重新生成简历。

## 交付记录

每轮报告：请求范围、读取资源、修改实体、影响产物、实际检查、未决项、下一步。报告不抄录整个资料库或秘密配置。
