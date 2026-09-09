# 本地运行

安全边界见[安全说明](../skill/resume-engineering/references/security.md)。同一工作区一次只执行一个写入操作。

撤回用途：`python skill/resume-engineering/scripts/pipeline.py revoke --workspace workspaces/demo --fact-id FACT-ID --use public_website`。只影响本地产物，外部副本需另行撤回。

安装requirements-dev.txt后，在仓库根目录运行：

```shell
python skill/resume-engineering/scripts/pipeline.py init-demo --workspace workspaces/demo --fixture examples/synthetic-person/workflow.json
python skill/resume-engineering/scripts/pipeline.py build --workspace workspaces/demo --targets website resume:process resume:npi resume:quality assistant
python skill/resume-engineering/scripts/assistant_server.py --workspace workspaces/demo --port 8765
```

打开 http://127.0.0.1:8765 。简历在workspaces/demo/exports/resume-*/index.html。不要把整个工作目录作为静态站点根目录；不提交workspaces。

增补流程：propose --candidate（完整Fact JSON），人工核对后accept；再次核对证据和用途后approve --fact-id --use --evidence-id。所有命令均需--workspace。不自动批准真实资料，旧证据不能自动证明新描述。

模型默认mock。真实接入时在私人进程环境配置AI_PROVIDER=openai-compatible、AI_API_URL（HTTPS聊天接口）、AI_API_KEY、AI_MODEL，以及可选AI_ALLOWED_ORIGINS准确来源白名单；不允许星号。不要将密钥写入公开文件。本轮未验证真实平台兼容性。

测试：`python -m unittest discover -s tests -v`。浏览器复验需Playwright和Chrome，可通过本地PLAYWRIGHT_MODULE、CHROME_PATH指定。先在output/workflow-demo生成目标并启动8765服务，再执行`node tests/render_workflow.cjs`。此测试不生成PDF。
