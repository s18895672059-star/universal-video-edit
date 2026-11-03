# 计划格式与组件

JSON 根字段：version=2；fps=60；output_size=[1920,1080]；crop、avatar_crop 为 [左,上,右,下] 的源画面归一化边界；scenes；captions；assets（可为空）；brand（可省略）；music.mode=none 或 synth。source、source_size、duration 由入口根据新素材更新。

scene 公共字段：start/end（绝对秒、全片无缝覆盖）；kind；title；sub（可省）；portrait；theme=light/dark/tech/gold；accent（十六进制颜色）；items（按组件需要）；eyebrow（可省）。transition=cut/fade/wipe/circle，transition_duration 默认 .35 秒。title_delay、content_delay、stagger、portrait_delay、portrait_duration 控制分层时间。portrait 可选 left/right/circle/circle_left/center/none；center 专供 interaction。crop/avatar_crop 可逐镜头覆盖。

|kind|实现与必需/可选字段|
|---|---|
|hook|本片场景缩略墙与标题；至少有一个非墙类场景|
|cards|1–3 个 items，错时卡片|
|bullets|1–4 个 items，编号分行|
|steps|1–6 个 items，流程连接与顺序入场|
|chat|1–3 个 items，逐段打字；typing_speed 默认 14 字/秒|
|file|1–3 个 items，层级文件卡与图标|
|timeline|最多 3 个 items 为轨道名，片段出现与游标移动；示意时间轴|
|collection|本片不同场景预览；卡墙不递归引用墙类场景|
|styles|1–3 个 items，样式比较卡|
|comparison|1–3 个 items，统一维度比较卡|
|metric|value 数字，data_note 数据来源或明确示意标注；prefix/suffix/decimals|
|quote|body 重点短语，footer 可省|
|code|lines 字符串列表，最多 7 行渐显|
|orbit|环形旋转图形和最多 3 个 items；概念图，不自动生成科学结论|
|curve|values 数列和 data_note，按值描线；注明单位/时间和数据来源|
|media|media=[资产ID]，保持素材比例；media_fit=contain 默认，cover 会裁切|
|triptych|media=[三个不同资产ID]，依次进场并独立播放；portrait=none|
|player|screen=真实界面图片ID、media=[视频ID]、player_box=[左,上,右,下]，坐标相对界面截图归一化|
|interaction|portrait=center；items 为 1–2 个侧边按钮短语；短时彩纸|
|gallery|两阶段推近选卡并接管下一场景；下一场景须非 gallery/hook/collection|
|end|body 大标题、footer 收束语|
|stamp|body 主句、stamp 斜印章短语|

所有文案均来自计划；渲染器不内置行业标题、品牌、价格、宣传口号。图形和布局可复用，不意味着将相同卡片用于所有内容。22类组件覆盖基础表达；styles 与 comparison 等共用部分卡片逻辑，不声称有22套完全不同的动画引擎。

## 字幕

每条：start、end、zh、en（可省或空）。highlights/en_highlights 为数组，每项 `{ "start": 1.2, "end": 1.8, "a": 0, "b": 2 }`，a 包含、b 不包含，表示该语言文本的字符范围，时间为全片绝对秒。中文和英文各自按实际口播语义对齐，不能机械每字等分。字段名 zh 为主行、en 为副行；主行也可使用其他语言。

字幕短语不重叠。长句拆分以免字号过小；不要把源视频里已经烧录的字幕再叠一份。先看原片再决定重排或保留。

## 资产

assets 示例：`{"demo":{"path":"media/demo.mp4","type":"video","offset":0}}`。图片 type=image。视频 size 和 duration 由入口检测并写入。offset 是资产的起始秒；超过片尾时保持末帧，不循环冒充新素材。外部资产不自动混入音轨。

player_box 必须按截图中真实播放器位置测量，不能让视频盖住菜单。triptych 不接受同一路径重复引用；需要同一长片不同段落时先提取成三个不同且有意义的片段。

## 明确的能力边界

原参考完整拆解见 full-relearning；当前组件未逐帧重建全部特定场景。三维倾斜卡、复杂软件操作、精确原片蒙版、镜头跟踪、多机位切换等需要在本次工程扩展。缩略墙的未选中卡是该场景静态预览；选中接管和主人物动态播放。要求墙内所有卡都动态时需增加多视频父级合成，不能把静态卡墙称作已实现此效果。

渲染器默认 16:9 SDR1080p，不能仅改数字就输出正确的竖屏布局。标题自动缩小有下限，超长会报错，应改文案或布局。字幕与人像路径仍需视觉验收，结构校验不会自动判断审美。
