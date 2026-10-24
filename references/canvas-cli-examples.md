# CLI 操作示例

配合 [画布执行](canvas-production.md) 使用。下列 shell 片段为 macOS/Linux 写法；Windows 可用 Python `subprocess` 参数列表执行同一 CLI。变量均须从本次真实返回或任务状态读取；新 UUID 只在首次创建该操作时生成并保存。不要直接逐段整页执行，不包含隐含的生成许可。

## 发现与创建

```bash
dreamina-canvas --version
dreamina-canvas schema
dreamina-canvas auth status
dreamina-canvas model find "$requested_model_name" --type video
dreamina-canvas canvas ls
```

需要认证才运行 `dreamina-canvas auth login`，沿返回的官方地址完成授权并复查。目标 profile 非默认时在全部命令中一致传 `--profile "$profile_name"`。根据用户现有账号环境确认 region，不从语言猜区域。

```bash
# project_uuid 在第一次调用前生成并持久化；创建失败时先查是否已存在。
dreamina-canvas canvas create "$canvas_name" --project-id "$project_uuid"
# 从返回 data.project 读取 project_id 和 webUrl，打开并发送 webUrl。
dreamina-canvas node find --project-id "$project_id" --type video
dreamina-canvas node show --project-id "$project_id" --node-id "$video_node_id"
```

`canvas ls` 返回 `data.items`，有 `hasMore` 时用返回的 `nextCursor` 续页。`node find` 只给摘要；从该次结果选 Node ID 后用 `node show` 读完整节点。名字不能代替写操作身份。

## 导入本地图、建立主体

```bash
# resource_uuid、image_node_id、import_submit_uuid、image_update_uuid 均先保存。
dreamina-canvas resource upload --project-id "$project_id" \
  --resource-id "$resource_uuid" --file "$character_image_path" \
  --type image --import-kind local_upload --name "$character_name"
# upload 成功后 resource_id = data.resourceId；不要拿签名 URL 当资源身份。
dreamina-canvas node create image --project-id "$project_id" \
  --node-id "$image_node_id" --update-id "$image_update_uuid" \
  --submit-id "$import_submit_uuid" --title "$character_name" \
  --resource-id "$resource_id" --import-kind local_upload
# main_image_node_id 指向同画布已就绪的媒体节点；没有辅助图就省略 auxiliary。
dreamina-canvas node create element --project-id "$project_id" \
  --node-id "$character_element_id" --update-id "$element_update_uuid" \
  --title "$character_name" --description "$identity_description" \
  --main "$main_image_node_id" --auxiliary "$auxiliary_image_node_id"
```

外部平台已生成的图按其实际来源将 import kind 设为 `external_generated`。同一张三视图是一个角色的多个角度，不是三个角色节点。图已在画布中时跳过上传/导入；直接用来源节点即可。

## 保存一个含多个子镜头的视频草稿

变量 `video_prompt` 是完整详细导演稿，其正文包含真实占位符，例如 `人物 A {{node:真实Element节点ID}}`。用代码字符串替换工程标记；不要让 shell 执行模型生成的正文。

```bash
dreamina-canvas node create video --project-id "$project_id" \
  --node-id "$video_node_id" --update-id "$video_update_uuid" \
  --title "$clip_title" --mode m2v --model "$canonical_video_model" \
  --ratio "$project_ratio" --resolution "$project_resolution" \
  --duration "$clip_duration_seconds" --count 1 \
  --prompt "$video_prompt" --ref "node:$character_element_id" \
  --ref "node:$scene_image_node_id"
dreamina-canvas node show --project-id "$project_id" --node-id "$video_node_id"
```

这是纯保存，不包含 `--run`。没有场景图就删去该 ref；没有任何参考的任务改用 `t2v` 并移除全部 ref/占位符。真实参数从 `model find` 和项目要求得出，不直接套示例型号。

多行长 prompt 推荐用 Python `Path.read_text()` 加 `subprocess.run([...])` 参数列表传递，不使用 `shell=True`、`eval` 或拼接 shell 命令。若只改参数，先回读并重新提交完整 generation，包括原先要保留的引用；不能只传新 duration 期待字段合并。

回读检查 `data.nodes` 中 FOUND 项的 `node.generation`、引用、正文定位与上游连线。人物参考就绪且参数正确才可进入运行阶段。

## 报价

```bash
dreamina-canvas node quote --project-id "$project_id" \
  --node-id "$video_node_id_1" --node-id "$video_node_id_2"
```

读取 `data.items[].maxCredits` 与 `data.totalMaxCredits`，核对节点清单完整、无单项 error。用户未批准时，先给出可审查的草稿和这份报价；批准上限来自人类许可，不来自 `confirmable=true`。

## 确认并提交的一次性调用

以下 Python 函数展示不回显 token 的调用方式。`state` 由 Agent 维护，`save_state` 必须原子保存且限制当前用户读取；节点 ID 与每项 submit ID 已在调用前落盘。**只在人工授权检查已完成、最新报价覆盖本批且没有任何不确定旧提交时调用一次。** `approved_ceiling` 是这一批已获授权的上限。不要把函数当成自动审批器。

```python
import json
import math
import subprocess


def valid_amount(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def submit_once(state, approved_ceiling, save_state):
    if state.get('submissionAttempted'):
        raise RuntimeError('先按原 submitId 查询任务，不重放运行')
    # 当前 CLI 的 credit-ceiling 是整数。拒绝缺值、NaN、无穷值、负数与布尔值。
    if not valid_amount(approved_ceiling) or int(approved_ceiling) != approved_ceiling:
        raise RuntimeError('批准上限必须是明确的有限非负整数')
    by_key = state.get('items')
    if not isinstance(by_key, dict) or not by_key:
        raise RuntimeError('批次 items 必须是非空业务键字典')
    items = list(by_key.values())  # 保留状态中明确的插入顺序
    if any(not isinstance(x, dict) or
           any(not isinstance(x.get(k), str) or not x[k].strip()
               for k in ('nodeId', 'submitId')) for x in items):
        raise RuntimeError('每项都必须有已保存的节点和提交身份')
    if (len({x['nodeId'] for x in items}) != len(items)
        or len({x['submitId'] for x in items}) != len(items)):
        raise RuntimeError('节点或提交身份重复；不能提交')
    common = ['--project-id', state['projectId']]
    nodes = [arg for item in items for arg in ('--node-id', item['nodeId'])]
    submits = [arg for item in items for arg in ('--submit-id', item['submitId'])]

    def invoke(args):
        # 不回显 args/stdout/stderr/envelope；异常的 cmd 也可能含 token。
        try:
            result = subprocess.run(
                ['dreamina-canvas', '--format', 'json', *args],
                capture_output=True, text=True, check=False, timeout=60)
        except (subprocess.TimeoutExpired, OSError):
            raise RuntimeError('CLI 传输未完成；保留状态并只读查询原任务') from None
        try:
            envelope = json.loads(result.stdout)
        except (ValueError, TypeError):
            raise RuntimeError('CLI 返回无法解析；保留状态，不重放运行') from None
        if (result.returncode != 0 or not isinstance(envelope, dict)
            or not envelope.get('ok') or not isinstance(envelope.get('data'), dict)):
            raise RuntimeError('CLI 调用未成功；保留状态，按结构化错误脱敏排查')
        return envelope['data']

    quote = invoke(['node', 'quote', *common, *nodes])
    rows = quote.get('items')
    if (quote.get('confirmable') is not True
        or not isinstance(rows, list) or len(rows) != len(items)
        or any(not isinstance(x, dict) or not isinstance(x.get('nodeId'), str)
               or x.get('error') is not None
               or not valid_amount(x.get('maxCredits')) for x in rows)
        or len({x['nodeId'] for x in rows}) != len(rows)
        or {x['nodeId'] for x in rows} != {x['nodeId'] for x in items}
        or not valid_amount(quote.get('totalMaxCredits'))
        or quote['totalMaxCredits'] > approved_ceiling):
        raise RuntimeError('批次报价缺失、无效、不可确认或超出上限；不能提交')
    confirmed = invoke(['node', 'confirm', *common, *nodes,
                        '--credit-ceiling', str(int(approved_ceiling))])
    token = confirmed.get('creditConfirmationToken')  # 仅内存
    if not isinstance(token, str) or not token:
        raise RuntimeError('未取得有效确认材料；不能提交')
    state['authorizedCreditCeiling'] = approved_ceiling
    state['submissionAttempted'] = True
    save_state(state)  # 在 run 前记录，响应丢失也有恢复入口
    result = invoke(['node', 'run', *common, *nodes, *submits,
                     '--credit-token', token])
    state['results'] = [
        {'nodeId': x['nodeId'], 'submitId': x['submitId'], 'state': x['state'],
         'resourceIds': [r['resourceId'] for r in x.get('resources', [])]}
        for x in result['items']]
    save_state(state)
    return state['results']  # 只返回公开任务事实
```

生产调用器还应从失败 envelope 中提取公开错误分类、`requiredAction`、`meta.requestId` 及 partialData 的恢复标识，不能因示例抛异常就重跑函数。`node run` 本身没有 `--credit-ceiling`；批量流程通过 `node confirm` 的 token 执行上限。单媒体 create/edit 的组合 `--run --credit-ceiling` 是另一种接口，不与纯 `node run` 混用。

## 查询和交付

```bash
# submit_id 是原生成任务 ID，不是 Node ID；查询不触发新的生成。
dreamina-canvas operation status "$submit_id" --project-id "$project_id"
dreamina-canvas operation wait "$submit_id" --project-id "$project_id" \
  --timeout 30s --interval 5s
dreamina-canvas resource get "$selected_resource_id" --project-id "$project_id"
# 仅当需要文件交付，output_path 为不会意外覆盖既有作品的目标路径。
dreamina-canvas resource download "$selected_resource_id" \
  --project-id "$project_id" --output "$output_path"
```

超时后可继续只读 wait，不能重新 run。中断时不需要重新授权已被受理的任务；尚无安全结论时保持未知状态，保留原 ID。节点的 `success` 与 operation 资源的 `succeeded` 等值按各自输出解释，不混用枚举。
