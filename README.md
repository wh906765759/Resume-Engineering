# Resume Engineering

以可追溯的职业事实为基础，管理个人网站、AI 职业助手和岗位简历的模块化 Skill。

当前版本：0.5.0，MIT许可本地发布包。已完成框架、模板、字段级事实投影、增量HTML生成、岗位排序、本地问答及部分安全加固。真实模型调用和生产部署尚未验收。[运行说明](docs/RUN_WORKFLOW.md) · [发布闸门](docs/RELEASE_GATE.md)。以下第二轮模板仍为静态演示，新生成流程使用独立工作区。

## 使用入口

阅读 [Skill](skill/resume-engineering/SKILL.md)，根据任务只加载对应模块。将 `skill/resume-engineering` 复制到支持本地 Skill 的工具目录后可调用 `$resume-engineering`；具体发现方式由目标平台决定，未声称所有平台均已验证。

使用者另建工作目录，保存 `project/`、`private/`、`facts/`、`approved/`、`website/`、`assistant/`、`resumes/`、`exports/`、`reports/`。不得在本公开工具仓库录入真实个人资料。

## 框架交付

- [架构及开发路线](docs/ARCHITECTURE.md)
- [模块契约](skill/resume-engineering/references/modules.md)
- [事实、词汇、照片与证据规范](skill/resume-engineering/references/data-contracts.md)
- [隐私与用途权限](skill/resume-engineering/references/privacy.md)
- [状态、依赖及增量更新](skill/resume-engineering/references/incremental.md)
- [阶段验收](skill/resume-engineering/references/acceptance.md)
- JSON Schema 位于 Skill 的 `assets/schemas/`；演示数据位于 `examples/synthetic-person/`，全部虚构。

## 第二轮模板

- [职业网站演示](skill/resume-engineering/assets/website-template/index.html)
- [两页简历演示](skill/resume-engineering/assets/resume-template/index.html)
- [视觉规范与照片流程](skill/resume-engineering/references/visual-templates.md)
- [素材来源记录](docs/ASSET_PROVENANCE.md)
- [第二轮验收报告](docs/ROUND_2_REVIEW.md)

双击HTML可本地预览；需保持assets目录结构完整。所有演示经历均虚构。AI问答为明确标记的固定演示，没有模型调用；照片为原创几何占位图。PDF可由浏览器打印生成，本地验收样本不自动公开。

视觉复验：安装Playwright并准备Chromium后运行 `node tests/render_templates.cjs`；默认使用已安装的playwright，支持用本地 `PLAYWRIGHT_MODULE` 和 `CHROME_PATH` 指向已有工具。输出位于忽略目录output，无个人目录硬编码。PNG由PDF渲染工具生成后人工复核。

## 框架验证

需要 Python 3.11+，安装开发验证依赖：`python -m pip install -r requirements-dev.txt`。

在仓库根目录运行：`python -m unittest discover -s tests -v`。

依赖用于验证，不是使用 Skill 文档的必要条件。网站、图像、PDF和模型工具在后续阶段单独声明。

## 发布范围

显示名称为Resume Engineering，Skill名为resume-engineering。第五轮已生成本地候选包；素材权利与MIT许可已确认，GitHub远程发布待完成。采用全新历史，不继承参考项目的源资料、账户配置或提交记录。打包清单与验证方式见发布闸门。
