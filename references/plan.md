# 剪辑方案

全部路径使用绝对路径。时间为毫秒，`trim_out` 是源素材的结束时间，不是片段长度。画布和 fps 必须为正整数。

```json
{
  "name": "演示剪辑",
  "width": 1280,
  "height": 720,
  "fps": 30,
  "keep_original_audio": true,
  "original_volume_db": -3,
  "clips": [
    {"path": "C:/Media/a.mp4", "trim_in": 500, "trim_out": 4500},
    {"path": "C:/Media/b.mp4", "trim_in": 1000, "trim_out": 5000}
  ],
  "captions": [
    {"text": "第一句话", "start": 0, "end": 3800, "x": 0, "y": -0.65, "scale": 0.56},
    {"text": "第二句话", "start": 4200, "end": 7800, "y": -0.65}
  ],
  "audio": [
    {"path": "C:/Media/bgm.wav", "start": 0, "trim_in": 0, "trim_out": 8000, "volume_db": -12, "fade_in": 300, "fade_out": 500}
  ]
}
```

- 顺序拼接，示例总时长 8000 ms。源视频必须有足够时长；字幕、配乐不能超出视频时间线。
- 图片片段使用 `path`、`kind: "image"`、`duration_ms`，本入口不生成图片运动。
- 原视频音量默认由 `original_volume_db` 决定；`keep_original_audio: false` 用 -120 dB 静音。片段 `gain_db` 或 `volume_db` 可覆盖默认值。
- 字幕 `x/y` 为相对画面中心的位置，范围 -1 到 1；`y` 为负表示靠下。`scale` 是必剪的比例，不是字体点数。不要用上游 `subtitle_size` 控制必剪字幕。
- 音频的 `start` 是时间线位置；`trim_in/trim_out` 是源音频范围。配乐太长时明确截短。
- SRT 转字幕时保留每条时间与文本，先校验其时间基准是否为剪辑后的时间线；不能直接把未剪源视频字幕时间复制过来。
- `prepare_draft.py` 对转场、显式片段 start、非 1 倍速和图片运动会报错，避免悄悄生成不同于要求的效果。高级需求可扩展底层 Timeline，但需要实际预览/导出验证。
