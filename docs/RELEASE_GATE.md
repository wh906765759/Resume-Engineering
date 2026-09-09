# 发布闸门

所有者已于2026-09-09确认模板样式对外分发权及MIT许可。根目录LICENSE适用于本工具；本地包就绪不等于已上传GitHub。

素材依据：ASSET_PROVENANCE.md。简历CSS来自所有者既有模板，已获得对外分发确认；字体、浏览器、Python环境不随包分发。

打包使用release-files.json逐文件白名单，而非递归上传整个工作目录。运行`python scripts/package_candidate.py`，输出ZIP、每文件SHA256与校验摘要到忽略目录output/release。

检查包括私钥标志、常见GitHub Token、Windows个人路径、邮箱和手机号格式；规则扫描不能证明绝无敏感信息，公开前仍要人工审阅白名单内容。报告和归档不自动上传。

解压后用当前Python环境执行全部测试并在新临时目录生成网站、简历和知识产物。这验证路径独立性，不等于在全新操作系统安装依赖，也不证明所有Agent平台可自动发现Skill。

安装使用skill/resume-engineering目录；演示初始化还需仓库examples目录及requirements-dev.txt。保留完整发布包以运行示例；不要将真实事实放入Skill安装目录。

GitHub技术仓库名拟为Resume-Engineering（显示名称Resume Engineering）。发布使用全新历史和明确文件清单，不使用git add .；提交身份应确认不泄露私人邮箱。当前未创建远程仓库。
