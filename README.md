# tilon-film-skill

让 Codex 把故事做成可执行、可审核的 AI 电影短片：角色定妆、表演节奏、有动机的运镜、即梦画布预生产与成片复核。

这是导演与制作流程 Skill，可配合已安装的 `dreamina-canvas` CLI，也可只输出脚本和提示词。不包含模型服务、账号或生成额度，不保证每次生成都没有变形或字幕。

## 安装

目标目录尚不存在时：

```bash
git clone https://github.com/benphant/tilon-film-skill.git ~/.codex/skills/tilon-film-skill
```

配置了不同 `CODEX_HOME` 时使用其 `skills/` 目录。刷新技能列表或重新打开会话后调用：

```text
使用 $tilon-film-skill 把这个故事做成 90 秒伪纪录片。
先准备角色和六段待生成画布，不提交视频任务；无字幕，保留采访与现场声音。
```

也可只诊断失败视频、只写可复制提示词，或按明确授权继续生成交付。时长、画幅、字幕、场景数都由项目决定。

## 方法

- 确认角色主图，再按需派生角度并绑定主体。
- 给对白、动作、倾听与反应安排可演的时间。
- 摄影机有目的、有路径、有结束构图，光线符合空间逻辑。
- 实际节点与提示词一致，执行前检查引用和授权范围。
- 观看及听取成片，记录缺陷，局部返修。

入口：[SKILL.md](SKILL.md)。来源及署名：[references/sources.md](references/sources.md)。

## 离线检查

Python 3.10+，无依赖、无网络调用：

```bash
python3 scripts/check_plan.py examples/plan.json
python3 -m unittest discover -s tests
```

检查时间、对白归属、角色引用与预生产状态，不验证真实语速或画质。

本仓库新编写的代码与文字使用 MIT。所引用原作保留各自许可，未包含第三方完整技能或媒体。
