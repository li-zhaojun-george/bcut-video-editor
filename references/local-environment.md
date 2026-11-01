# 环境配置

验证平台：Windows，必剪 3.11.25.100。其他版本需要重新做小样导出验证。

使用 Python 3.10+、Pillow，以及 ffmpeg.exe 和同目录的 ffprobe.exe。必剪安装目录会从注册表和常见位置自动发现，默认草稿库是当前用户 Documents/Bcut Drafts。

必要时设置进程级环境变量（以下为示例路径，需替换）：

```powershell
$env:BCUT_HOME='C:\Apps\BcutBilibili'
$env:BCUT_FFMPEG='C:\ffmpeg\bin'
$env:BCUT_EDIT_TMP=Join-Path $PWD 'bcut-work'
```

- BCUT_HOME：包含 BCUT.exe、Font 和 res 的必剪安装目录。
- BCUT_FFMPEG：FFmpeg 目录，或 ffmpeg.exe 的绝对路径；ffprobe.exe 应在同目录。
- BCUT_LOCAL_RES：可选的必剪 local_res 目录覆盖。
- BCUT_DRAFT_ROOT：读取或生成时的草稿目录覆盖。生成使用 prepare_draft.py 的工作区暂存目录，注册再明确指定实际草稿库。
- BCUT_EDIT_TMP：工作区临时输出目录。不要把 skill 目录用于存储媒体。

运行 `python -X utf8 scripts/bcut.py doctor` 检查发现结果。字体和 speech 模板来自用户已安装的必剪；本仓库不分发必剪程序、字体、FFmpeg 或媒体素材。
