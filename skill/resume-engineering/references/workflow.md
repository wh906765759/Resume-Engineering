# 事实驱动工作流

工作目录必须独立于Skill与公开仓库。脚本位于scripts，依赖Python 3.11+和jsonschema。先读project/state.json模块总状态，再读run-state.json最近操作及build-manifest.json来源摘要。只加载本次影响的事实和模块。

facts/facts.json保存事实；project/plan.json通过`{"$fact":"事实ID","field":"result"}`绑定展示字段。包括Title、日期、数字在内的文字均需证据和用途批准，不允许直接插入未绑定文本。当前数据形状参考公开仓库examples/synthetic-person/workflow.json；模板只支持约定结构。

pipeline.py propose生成差异，用户审阅后才accept；accept递增版本、保留证据并重置权限。用户确认事实及用途后才能approve，不可为通过生成而自动批准。build指定website、assistant、resume:process等目标。岗位策略当前仅调整项目和能力排序。

指纹检查事实、权限、模板和策略，文件哈希检查产物完整性。过期输出转入private/quarantine，不删除；该机制不撤回已经上传外部站点的副本，外部撤回须单独获得授权执行。

assistant_server.py仅监听本机，默认mock不访问第三方。每次请求重新评估public_ai权限，模型返回后再检查。来源白名单不等于认证；引用编号校验不保证模型语义正确。真实模型和生产安全必须另行验收。

不要默认扫描全库作为模型上下文。生成器确定性处理不调用模型；用依赖和运行摘要缩小下一轮读取范围，不承诺未经测量的Token节省比例。
