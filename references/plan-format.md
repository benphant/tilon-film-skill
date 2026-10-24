# 离线计划格式

`python3 scripts/check_plan.py examples/plan.json` 只读本地 JSON。退出码 0 为结构检查通过，1 为计划错误，2 为文件或 JSON 无法读取。不会打开画布、生成媒体、申请授权或访问网络。

新计划使用 `schema_version: 2`。`shots` 沿用工程字段名，表示独立生成片段，不表示内部只能有一个摄影镜头。每个片段中的 `subshots` 才是按秒拆分的子镜头；例如 15 秒片段拆成 0–3、3–8、8–12、12–15 秒。时间以片段起点为零，必须有序、无空隙、无重叠并覆盖片段总长。需要一镜到底时，子项可代表连续调度阶段，`transition` 写清“不剪切”及衔接动作。

## 全局字段

- `stage`：`script`、`preproduction`、`production` 或 `review`。
- `audio`：显式声明 `bgm`、`subtitles` 两个布尔值。本项目默认都为 `false`；用户明确需要时可以为 `true`。检查器只要求声明，不覆盖用户选择。
- `shots`：至少一个独立生成片段。

## 每个生成片段

- `id`：非空且在计划内唯一。
- `duration`：大于零的秒数。若填写从画布读回的 `node_duration`，必须相等。
- `ratio`：例如 `16:9`。若填写从画布读回的 `node_ratio`，必须与脚本一致。检查器不判断模型是否支持此画幅。
- `status`：在 `preproduction` 阶段必须为 `draft`，防止把已经生成的节点误报为待审核草稿。
- `characters`：角色编号数组，可为空。
- `continuity_required`：需要视觉来源保持身份的角色编号；必须属于 `characters`。单次原创文生视频可以为空，不为完成检查而强造人物图。
- `references`：已记录视觉来源的角色编号数组。预生产、生产和复核阶段，`continuity_required` 中每个角色必须在其中。它只是本地声明，不能证明画布节点已真实连线、素材已就绪或主体绑定正确；这些还要用 CLI 回读核验。
- `subshots`：每项包含 `start`、`end`，以及非空的 `scene`、`blocking`、`action`、`performance`、`camera`、`lighting`、`background`、`sound`、`transition`、`continuity`。这些字段分别承载时间地点及服化道、站位、动作、表演、摄影、光线、背景、声音、转场和终态。无人物时写明无人物表演，固定机位写明固定，不用空字段冒充已规划。
- `dialogue`：可为空；每句含 `start`、`end`、`speaker`、`text`。说话者必须是已列角色或 `VO`，可附 `delivery` 说明录音、画外或内心独白。对白可以跨子镜延续，但不得超出整个生成片段。
- `allow_overlap`：默认 `false`；明确设计叠话时设为布尔值 `true`，并在导演稿中交代主次。字符串 `"false"` 不合法。

无 `schema_version` 或值为 1 的旧 `shots/beats` 格式仍能读取，会提示升级详细调度字段。旧格式也只要求 `continuity_required` 指定的角色有参考，不再强迫所有预生产角色创建主体。

结构通过不证明描述足够具体、不证明对白语速可演、不证明节点真的引用素材，也不证明成片无字幕、无BGM或具有电影质感。导演审稿、画布回读和真实音画审片是另外三项工作。
