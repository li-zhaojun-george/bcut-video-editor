---
name: bcut-edit
description: 在 Windows 上根据本地素材和剪辑要求生成必剪可编辑草稿，支持顺序裁剪拼接、中文字幕和配乐，并在必剪中验证与导出。适用于必剪工程自动化；不用于 B 站投稿或云端字幕 API。
metadata:
  short-description: 生成必剪草稿，验证字幕音轨并协助导出
---

# 必剪草稿剪辑

把用户的剪辑要求转为本地时间线，生成独立必剪草稿，再由必剪预览和导出。脚本来自 MIT 项目 dsh-bcut-edit，并包含 Windows 必剪 3.11 的本机适配。来源与验证范围见 [references/compatibility.md](references/compatibility.md)。

在必剪 3.11.25.100 上已通过原生导出验证的基础流程：视频裁剪拼接、两条中文字幕、外部音轨及淡入淡出。生成草稿可自动完成；电脑控制不可用时，预览和导出需要用户在必剪操作。

## 准备

- 优先读取素材、草稿目录和用户已有剪辑要求；只询问会影响成片的缺失信息。默认生成新草稿，保留原作品。
- 使用 Python 3.9+、Pillow，以及可用的 ffmpeg.exe 和 ffprobe.exe。不要因 PATH 未配置而重装现成工具。
- 命令中的 `SKILL` 表示本文件所在目录。先读 [references/local-environment.md](references/local-environment.md) 配置或发现当前电脑的工具路径。
- 用进程级环境变量设置 `BCUT_FFMPEG`（目录或 ffmpeg.exe）、`BCUT_HOME`（必要时）和位于当前工作区的 `BCUT_EDIT_TMP`。使用 `python -X utf8` 避免中文编码错误。
- 素材和字幕只使用本次用户明确提供或授权使用的内容；不要把演示方案、其他草稿或技能目录里的模板文字当作用户素材。发现本机缺少资源时重新配置或报错，不引用发布者机器上的路径。
- `python -X utf8 "$SKILL/scripts/bcut.py" doctor` 检查工具。读取草稿前取消临时的 `BCUT_DRAFT_ROOT`，或明确指向实际草稿库。`drafts` 列表只作读取，`show GUID` 使用修改时间最新的快照。

## 生成与注册

1. 根据 [references/plan.md](references/plan.md) 保存 UTF-8 JSON 剪辑方案，素材使用绝对路径。时间单位为毫秒。已验证的生成入口面向普通速度的顺序片段、静态图片、字幕和音频。高级转场、多轨叠加、变速等应单独做小样验证，不能把上游声称支持当成本机通过。
2. 在当前工作区构建：
   `python -X utf8 "$SKILL/scripts/prepare_draft.py" plan.json --output prepared-drafts`
   保存返回的 GUID。此入口校验媒体与时间范围，只新增草稿。
3. 检查生成 JSON、素材路径、字幕及音频范围。草稿引用素材原路径；不要随后清理或移动这些素材。
4. 注册前让必剪正常退出，避免它用内存中的旧索引覆盖外部写入。不要强杀正在编辑的程序。运行：
   `python -X utf8 "$SKILL/scripts/register_draft.py" --source prepared-drafts --guid GUID --destination "实际草稿库" --backup-dir backups`
   脚本备份索引、保留原条目，并拒绝覆盖已有 GUID。操作已经包含在用户的剪辑任务授权中时，不重复索要同一授权；遵守实际文件写入权限。
5. 打开新草稿，检查片段顺序、字幕显示、音频缺失提示和声音。若电脑控制可用，按 computer-use 技能操作。快照增加只证明必剪保存过，不证明画面、声音正确。
6. 导出到工作区后，使用 FFprobe 检查时长、分辨率和音视频流；提取字幕时段的帧、检查音频信号，必要时试听。仅创建工程不能报告为导出成功。

## 修改与故障处理

- 修改本技能生成的作品也创建新 GUID。用户已在必剪手工修改过的草稿，先读取和保留其副本；不要从旧 plan 重建后声称保留了手改。
- 字幕轨存在但画面不显示：检查字幕是否被视频覆盖。视频和字幕共用从下到上的 `index`，字幕编号应大于视频；主视频轨 `split=true`。同时检查 `assetInfo.srcPath` 指向安装目录的 `res/subtt/huazi/speech`，字体存在，且 `textFrameOriginRect` 非零。不要用重命名文件后缀解决。
- 音频在素材栏显示缺失：除文件存在外，检查素材表 `itemType=5`，音轨 `assetInfo.type=2`、`audioType=1`。这些字段已有修正。
- 预览正常、导出第 0 帧报错误码 7：读取本机 `AppData/Local/BCUT/log/montage_log/montage_1.log`。若出现 `set crop params ... inf`、错误 913，检查 `propertyFxList` 是否有零尺寸 crop，并清除从旧 `businessType=2` 效果转换来的无效裁剪；在新的 GUID 中修复。此错误不应直接归因于显卡或要求重装软件。
- 画面捕获出现 `FrameArrived timed out` 时，按电脑控制技能做有限恢复；不得用陈旧坐标点击。若系统应用也失败，让用户预览或导出，再检查本地产物。清楚区分用户确认、静态检查与实际导出验证。
- `bcut.py render` 是上游 FFmpeg 后端，未纳入本技能已验证流程；其时间和效果不保证与必剪相同，不作为必剪原生导出的替代证据。

用户要求的最终产物应包括可编辑草稿名称、素材/成片位置、验证结果以及仍未验证的功能。生成草稿或导出本地视频不包含发布到 B 站的授权。
