# tilon-film-skill

让 Codex 把故事写成逐秒、逐子镜头的详细调度，并推进即梦画布制作：表演、服化道、空间、摄影、光线、声音、参考绑定与预算执行。

这是导演与制作流程 Skill，可配合已安装的 `dreamina-canvas` CLI，也可只输出脚本和提示词。不包含模型服务、账号或生成额度，不保证每次生成都没有变形或字幕。

## 安装

目标目录尚不存在时：

```bash
git clone https://github.com/benphant/tilon-film-skill.git ~/.codex/skills/tilon-film-skill
```

配置了不同 `CODEX_HOME` 时使用其 `skills/` 目录。刷新技能列表或重新打开会话后调用：

```text
使用 $tilon-film-skill 把这个故事做成 90 秒伪纪录片。
16:9，每段 15 秒，段内按动作拆子镜头，写清表情、站位、光线与运镜。
先准备角色和六段待生成画布，我来点生成；无 BGM、无字幕。
```

也可只诊断失败视频、只写可复制提示词，或按已有授权继续生成交付。默认无 BGM、无字幕；用户可明确修改。时长、画幅、模型和题材由项目决定，不把案例中的竖屏都市剧套到所有任务。

## 方法

- 一个 15 秒生成片段可以拆为 3+5+4+3 秒的子镜头，连续覆盖时间，不只写对白。
- 每个子镜头控制人物的眼神、微表情、动作先后、站位、道具归属与服装状态。
- 摄影机有信息动机、起终点、距离、路径与适量呼吸，固定光源和背景活动遵守空间逻辑。
- 导演稿保留详细调度，模型提示词突出视觉中心与落点；复杂接触写清先后，简单场面不额外堆事件。
- 三视图需要时是一张图里的同一人三角度；角色通过真实媒体引用传递，名称不能代替绑定。
- 画布流程覆盖新建/复用、导入、主体、正文引用、保存草稿、报价授权、提交与中断恢复。
- 区分已保存、已受理、生成完成与审片通过，不盲目重复扣费。

入口：[SKILL.md](SKILL.md) · [详细调度模板](references/detailed-shot-template.md) · [聚焦与提示词编译](references/focus-and-prompt-compilation.md) · [渡轮与托盘示例](examples/focused-prompts.md) · [完整 15 秒样例](examples/detailed-15s.txt) · [画布操作](references/canvas-production.md) · [来源及署名](references/sources.md)。

## 离线检查

Python 3.10+，无依赖、无网络调用：

```bash
python3 scripts/check_plan.py examples/plan.json
python3 -m unittest discover -s tests
```

详细格式见 [plan-format.md](references/plan-format.md)。检查子镜头完整性、时间、对白归属、画幅、声明的角色引用与预生产状态；不验证真实语速、媒体实际绑定或画质。

本仓库新编写的代码与文字使用 MIT。所引用原作保留各自许可，未包含第三方完整技能或媒体。
