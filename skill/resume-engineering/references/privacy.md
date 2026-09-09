# 隐私与用途规则

privacy_level: public_candidate / internal / restricted。public_candidate仅表示可以提交公开审核，不是默认授权。
用途: private_storage / targeted_resume / public_website / public_ai。每条事实四个用途均有独立决策，默认deny。

## 有效输出条件

1. 事实status=verified且无未解决冲突。
2. 对应用途decision=allow，批准包含review_id、evidence_ref、时间和当前fact_version。
3. internal仅可在明确批准后进入定向投递；restricted只能private_storage。
4. 公开用途要求privacy_level=public_candidate；来源、证据路径和内部审核元数据不得随内容自动输出。

不满足任一条件时拒绝进入该用途产物。需要脱敏时建立有来源的派生事实并单独审核，不能仅靠改privacy_level绕过原边界。

## 需要核查的内容

内部项目编号、客户身份、未公开参数、商业指标、内部流程、文件路径、系统截图、照片授权、个人联系方式、未发表研究或未提交专利。真实不等于可公开。

简历公开下载属于public_website，即使文件最初是为targeted_resume生成，也需再次审核。网站获准内容不自动进入public_ai。API密钥永远不属于职业事实，保存在运行环境秘密管理机制。

## 撤回和变更

事实更正或权限撤回后，依赖图标记下游stale/quarantined，阻止新发布；对已发布副本生成撤回/替换任务并按既有授权处理。记录状态不能证明互联网缓存已清除。不得静默保留过期知识索引或旧附件作为当前版本。

## 公开Skill发布

使用全新仓库历史。检查待发布文本、二进制元数据、EXIF、隐藏层、source map、脚本常量与Git历史。扫描无匹配不证明绝对无泄露，还需人工复核。只包含占位数据/标明虚构的样例，不携带真实用户内容和账户标识。
