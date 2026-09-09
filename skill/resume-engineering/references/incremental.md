# 状态与增量更新

工作目录project/state.json符合 [状态Schema](../assets/schemas/state.schema.json)，project/dependencies.json符合 [依赖Schema](../assets/schemas/dependencies.schema.json)。状态和图均私人。

## 会话恢复

先读状态摘要及本轮模块索引；依据modified版本/哈希核对相关文件。摘要有来源引用，不能取代事实。状态与文件不一致时标记stale并核实，不沿用上轮“通过”。禁止默认读取全部历史对话、全部原始资料或全部参考文档。

## 依赖方向

边from为输入，to为派生产物，source_version为消费时版本。输入可以是事实、词汇、照片、模板、配置、审核记录或其他产物。
修改输入时沿出边计算传递闭包；图中节点唯一、边不能悬空、不能成环。发布器必须拒绝依赖旧版本、权限失效、状态非ready或追溯不完整的产物。

依赖缺失不能推断无影响：检索受影响模块的引用，并将未确定项报告为unknown。尚未实现自动发布器，以上是后续实现的强制契约。

## 每轮记录

保存change_id、request、module_scope、changed_ids、impacted_ids、input_versions、checks、unresolved、outputs与状态。state记录引用该变更文件，不累积整库文本。
module状态: not_started / in_progress / blocked / ready / stale。blocked给出实际阻碍；ready需有产物引用和验收记录。产物状态: draft / ready / stale / quarantined。

## 令牌与重复工作

预先列最小读取集合；脚本输出计数与失败ID，成功时不倾倒正文。内容未变用哈希复用；共享样式改变需视觉复验而非重写文字。记录read_files、changed_files、regenerated_outputs、token_usage；不可获得token_usage时为null，不估算节省百分比。

权限撤回需要传递检查，即使耗时增加也不能只检查局部直接引用。Token节省服从事实正确性和发布边界。
