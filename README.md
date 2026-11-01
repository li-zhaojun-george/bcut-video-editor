# bcut-video-editor

让 Codex 根据本地素材生成**必剪（Bilibili BCUT）可编辑草稿**，支持顺序裁剪拼接、中文字幕和音轨，再在必剪中预览、微调和导出。

这是基于 [dsh-bcut-edit](https://github.com/LQH-A-A-O/dsh-bcut-edit) 的 Codex 适配版本，采用 MIT 许可证。已在 **Windows / 必剪 3.11.25.100** 上完成基础流程的原生导出验证；不是 Bilibili 官方插件。

仓库名为 `bcut-video-editor`，Codex skill 名称为 **`bcut-edit`**。

## 已验证的功能

- 按毫秒范围裁剪视频，顺序拼接为独立工程。
- 创建可编辑中文字幕，设置时间、位置和比例。
- 加入本地音频，设置音量、截取范围及淡入淡出。
- 在工作区暂存草稿，必剪退出后备份索引并注册新 GUID。
- 保留已有草稿，不覆盖用户工程或已有 GUID。

基础流程已通过原生导出检查，字幕可见、音轨有效且成片完整解码。验证范围及边界见 [兼容性记录](references/compatibility.md)。

高级转场、多轨叠加、变速和不同后端的效果一致性尚未完成原生验收。`prepare_draft.py` 会拒绝已知未支持的方案选项，避免悄悄忽略效果。

## 安装为 Codex skill

需要 Windows、已安装的必剪、Python 3.10+、Pillow，以及 ffmpeg.exe / ffprobe.exe。本仓库不包含必剪程序、字体或 FFmpeg。

在 PowerShell 中执行：

```powershell
$skillsRoot = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
} else {
    Join-Path $env:USERPROFILE '.codex\skills'
}
$skillPath = Join-Path $skillsRoot 'bcut-edit'
git clone https://github.com/li-zhaojun-george/bcut-video-editor.git $skillPath
python -m pip install -r (Join-Path $skillPath 'requirements.txt')
```

如果该目录已存在，请先保留已有版本；上述命令用于全新安装。让 Codex 重新加载技能后，可以直接说：

> 使用 $bcut-edit，把这些素材剪成视频，添加中文字幕和配乐。

Skill 会读取 [SKILL.md](SKILL.md) 执行工作。首次使用按 [环境配置](references/local-environment.md) 检查工具路径。

## 命令行流程

以下命令在仓库根目录运行。将 FFmpeg 路径和素材路径替换为自己的实际路径。

```powershell
$env:BCUT_FFMPEG='C:\ffmpeg\bin'
$env:BCUT_EDIT_TMP=Join-Path $PWD 'bcut-work'
python -X utf8 scripts/bcut.py doctor
```

复制 [examples/plan.json](examples/plan.json)，填写本地素材的绝对路径。示例需要两段各至少 5 秒的视频和至少 8 秒的音频；时间单位为毫秒。完整字段说明见 [剪辑方案](references/plan.md)。

```powershell
python -X utf8 scripts/prepare_draft.py examples/plan.json --output prepared-drafts
```

命令返回新草稿的 GUID。**正常退出必剪**，再把该 GUID 填入注册命令：

```powershell
python -X utf8 scripts/register_draft.py --source prepared-drafts --guid '返回的 GUID' --destination (Join-Path $env:USERPROFILE 'Documents\Bcut Drafts') --backup-dir backups
```

草稿目录经过重定向或自定义时，应使用实际目录。脚本检测到必剪仍在运行时会拒绝注册，并在写入前备份 `draftInfo.json`。工程引用源媒体路径，因此请保留源媒体。

打开必剪中的新工程，检查画面、字幕和声音，再导出到自己的工作区。生成工程、预览正常和原生导出成功是不同的验证阶段。导出后应检查时长、音视频流，以及字幕时段的实际画面。

**本项目不提供无人值守的原生导出接口。** Codex 电脑控制可用时可协助操作；不可用时，需要用户在必剪中预览和导出。上游保留的 `bcut.py render` 使用 FFmpeg 后端，不作为必剪原生导出的验证证据。

## 本版本的兼容性修复

| 问题 | 修复 |
| --- | --- |
| 导出第 0 帧失败，错误码 7 / SDK 913 | 移除旧模板会转换成零尺寸裁剪的效果，使用有效的裁剪字段 |
| 字幕轨存在，但成片无文字 | 视频与字幕共用不冲突的视觉轨道编号，字幕位于视频上方；同步主轨设置与显示顺序 |
| 字幕资源不完整 | 补齐本地 speech 模板路径和文本画布矩形 |
| 音频素材显示缺失 | 修正音频素材类型和本地音轨元数据 |
| FFmpeg 环境变量指向 exe 后探测失败 | 正确寻找同目录 FFprobe |
| 草稿跨午夜读取旧快照 | 按修改时间选择最新快照 |

## 来源与许可证

派生自 [LQH-A-A-O/dsh-bcut-edit](https://github.com/LQH-A-A-O/dsh-bcut-edit)，固定上游提交 [`8cbd464976aa8babe2c88312eb915e4a15e3680a`](https://github.com/LQH-A-A-O/dsh-bcut-edit/commit/8cbd464976aa8babe2c88312eb915e4a15e3680a)。保留上游版权声明及 [MIT LICENSE](LICENSE)。Codex 适配修改见 [兼容性记录](references/compatibility.md)。

发布包包含脚本、JSON 格式模板、资源目录和文档；不包含个人草稿、源视频、导出视频、电脑日志或本机配置。使用必剪内置资源时，仍需本机已安装相应资源。

## 发布前检查

```powershell
python -X utf8 scripts/check_distribution.py
python -X utf8 -m unittest discover -s tests -v
```

检查发布文件和模板残留，并用两个临时配置验证素材/字体路径及新工程编号隔离。测试不接触实际草稿库。数据边界和检查限制见 [隐私与数据隔离](references/privacy.md)。
