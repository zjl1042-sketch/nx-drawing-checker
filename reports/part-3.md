# 球面端盖：光滑内腔 · 读图与模型校核

单位：mm

## 视图

- **plan**（orthographic）：接管、立板、安装耳的平面位置
- **isometric**（isometric）：凸台和立板位于外表面
- **front**（orthographic）：正视图：外 R90 实线轮廓、内 R85 虚线轮廓，球心距底面36；原图未给剖面线，不称作正式剖视图

## 特征与证据

### R85 球面内腔

void · cavity

- front：R85 内弧连续；外部接管及立板下方没有伸入内腔的额外实体轮廓。
- plan：用于确定接管与立板方位，检查这些外部特征对应的内腔位置。
- isometric：接管和立板是球壳外部特征，内部形状仍以正视图中的内轮廓虚线为依据。
- 深度依据（hidden_lines）：正视图中的 R85 隐藏内轮廓和接管内壁虚线用于判断内腔；与俯视口形共同核对，不把轴测图作为深度依据。
- 内球半径 = 85（stated，front）
- 外球半径 = 90（stated，front）
- 球心 z = -36（stated，front）

### 偏置长圆接管通内腔

void · through

- front：左侧接管内壁向下连入球壳内腔；42 标注定位右端圆心，孔下不应保留底板。
- plan：外轮廓 R12、内孔 R8，两端圆心距19。
- isometric：偏置接管顶面呈完整长圆开口；轴测图只支持口形，深度结合正视内轮廓确定。
- 深度依据（hidden_lines）：正视图中的 R85 隐藏内轮廓和接管内壁虚线用于判断内腔；与俯视口形共同核对，不把轴测图作为深度依据。
- 内孔端半径 = 8（stated，plan）
- 端圆心距 = 19（stated，plan）
- 右端圆心距主轴 = 42（stated，front）

## 读图检查

通过


## 模型几何检查

- 通过：R85 球面内腔 / 内腔没有伸入材料，0/300 cavity test points contain solid
- 通过：R85 球面内腔 / 内壁落在 R85 球面上，0/18 inner-wall rays deviate from R85.0 by more than 0.6 mm
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-66 y=0 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-61 y=0 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-55 y=0 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-49 y=0 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-42 y=0 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-37 y=0 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-61 y=5 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-61 y=-5 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-42 y=5 贯通，0 surface crossings
- 通过：偏置长圆接管通内腔 / 长圆孔 x=-42 y=-5 贯通，0 surface crossings
- 通过：NX 建模历史 / 单位，mm
- 通过：NX 建模历史 / 实体数量，1
- 通过：NX 建模历史 / NX 特征错误，0 条错误
- 通过：NX 建模历史 / SKETCH 数量，2，至少 2
- 通过：NX 建模历史 / EXTRUDE 数量，3，至少 3
- 通过：NX 建模历史 / SWP104 数量，2，至少 2
- 通过：NX 建模历史 / 内壁修正，1 个匹配特征
- 通过：NX 建模历史 / 长圆孔，1 个匹配特征
