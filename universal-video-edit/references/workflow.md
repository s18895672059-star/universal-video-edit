# 在新电脑使用

将 ZIP 与用户新视频一起交给 Codex：

> 解压并使用 universal-video-edit/SKILL.md，按这条视频的实际内容完整剪辑。重新转写、设计分镜和字幕，使用包内参考风格与组件，保证人物清晰。不要使用任何示例文案和行业数据。完成预览检查和高质量渲染，交付 MP4 与编辑计划。

不依赖旧聊天和旧工程目录。无需把本 Skill 永久安装到系统；解压后按文件使用即可。仅在用户要求安装时复制到其技能目录。

## 环境

Python 3.11/3.12，Windows、macOS 或 Linux；本次开发验证平台为 Windows。使用本机 Python 创建虚拟环境，命令中的 python 换成虚拟环境解释器。

```text
python -m venv .venv
python -m pip install -r scripts/requirements.txt
python scripts/edit.py doctor
```

先激活 `.venv` 再执行 pip。需要本地语音识别时安装 `scripts/requirements-asr.txt`。依赖采用兼容版本范围，实际验证版本记录在 validation.md，不承诺未来所有组合兼容。

FFmpeg 从 EDIT_FFMPEG、PATH、imageio-ffmpeg 依次选择；需要 libx264。中文字体默认取 Windows 的微软雅黑。跨系统通过 `EDIT_FONT_REGULAR`、`EDIT_FONT_BOLD` 指定本机合法可用的中英文字体文件绝对路径，或 `EDIT_FONT_DIR` 指定含 msyh.ttc/msyhbd.ttc 的目录。不随包分发商业字体。字体变化会改变排版，必须重新预览。

## 素材与转写

```text
python scripts/edit.py prepare "input.mp4" "project"
```

生成 source-info.json、三个原尺寸抽帧、audio.wav、transcript.jsonl。本地识别默认自动检测语言、使用 faster-whisper small，首次需联网下载模型。`EDIT_WHISPER_MODEL` 可指定本地模型路径或模型名；`EDIT_LANGUAGE` 可指定 zh/en 等语言。若 Codex 已有可靠转写工具，可代替此步骤，仍要检查原始画面和技术参数。

自动识别必须人工校对人名、术语、数字、停顿和短语切分。转写只产生时间文本，不自动做分镜或可靠的中英翻译。

## 编排与素材

按 components.md 在 project 写 edit-plan.json，按新原视频安排时长，不能直接拿示例时间套新视频。所有外部资产放在 project/media/，资产路径相对 project。原片文件路径由入口命令指定，自动写入计划。

对每条视频观察人物全身运动范围；crop/avatar_crop 为源画面归一化裁切框，可逐镜头覆盖。不要沿用示例框。自动脚本不会识别人脸或自动跟踪。

外部视频的尺寸与时长由入口更新。视频旋转/HDR检查不通过时，先在明确色彩与方向要求后处理输入，或改用能保留该要求的渲染工程；不要仅修改标签伪装转换。原文件始终保留。

```text
python scripts/edit.py validate "input.mp4" "project"
python scripts/edit.py preview "input.mp4" "project"
python scripts/edit.py render "input.mp4" "project"
```

preview 为每段生成进入、运动与停留阶段的 3 张帧。它只能发现部分排版问题；动作衔接还要渲染样段观察。render 输出 final_1080p60.mp4，检查全片解码、分辨率、帧率和时长，生成 export-report.json。

## 声音与发布

默认保留原声，音乐默认关闭。music.mode=synth 时使用脚本合成的低音量配乐并在人声时自动压低；配乐不是原片音乐。用户提供的音乐需单独接入混音并确认人声清楚。发布用最终原始导出文件，不经聊天软件二次压缩。此渲染器不包含自动上传功能。

## 扩展

22类组件不是一套固定镜头顺序。Codex 需要在本次工程副本中扩展新组件时，修改 film.py 对应分支、schema.py 的校验和计划字段，并补充相应预览。参考拆解覆盖的动作比基础渲染器更多；不应把“脚本尚无组件”解释成可以省略用户要求的效果。

新电脑可执行 `python scripts/test_components.py "全新测试目录"`，自动生成测试色条素材并预览全部22类组件。加 `--render` 会导出44秒测试片，耗时取决于CPU。它是技术测试，不是成片审美示例；真实界面、人物和产品仍由用户提供。
