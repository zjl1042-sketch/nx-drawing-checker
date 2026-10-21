# NX Drawing Checker

[English](README.en.md) · [可复现演示](examples/README.md) · [贡献指南](CONTRIBUTING.md) · [MIT License](LICENSE)

从机械零件图建立可追溯的特征判断，并用模型几何检查通孔、空腔与内壁。

本项目用于解决两类实际误读：把贯通开窗做成带底凹槽；让外部凸台或立板伸入本应光滑的球面内腔。流程是 **提取原图 → 分视图 → 写出判断依据 → 建模 → 剖切及几何验证**。

工具不会自动证明读图判断正确。它要求把判断写出来，检查缺失的证据，并让关键判断有可运行的模型验证。低分辨率原图的缺失细节也不能通过放大恢复。

## 安装

需要 Python 3.10 或更新版本。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
source .venv/bin/activate
```

Windows 下使用 `.venv\Scripts\python.exe`，并通过 `.venv\Scripts\nx-drawing-checker.exe` 调用命令。本工具仅依赖 Pillow；NX 日志需要在安装了 NX 的机器中执行。

## 无需 NX 的公开演示

安装后运行：

```bash
python examples/synthetic_demo.py
```

演示生成合成封闭网格，验证“阻挡贯通线时拒绝，移除阻挡后通过”，不需要私有图纸或 NX。
合成案例不代表真实工程读图准确率；具体说明见 [examples/README.md](examples/README.md)。

## 使用

原始作业文件及 NX 模型留在本地，`work/` 不提交到 Git。

```bash
nx-drawing-checker extract "作业.docx" work
nx-drawing-checker crop cases/part-2.json work/part-2-views
nx-drawing-checker review cases/part-2.json --report work/part-2-review.md
nx-drawing-checker check-stl cases/part-2.json work/part-2.stl \
  --history work/part-2.stl.history.json --report work/part-2-check.md
nx-drawing-checker preview work/part-2.stl work/part-2-projections \
  --section-axis y --section-position 25
```

`extract` 按文档中的出现顺序提取嵌入图像，保留原始字节、分辨率与 SHA-256。`crop` 按案例给出的矩形裁剪，保留原始像素，不做会改变线条的生成式增强。

`review` 检查每个空腔是否明确标为贯通、盲孔或内腔，是否引用至少两个视图，是否明确记录深度依据，是否有建模后检查。图上已标尺寸与估计尺寸必须分别注明；估计尺寸要写依据。深度依据 `depth_basis` 可为 `section`（正式剖视）、`hidden_lines`（正投影视图的隐藏轮廓）、`callout`（明确深度/贯通标注）或 `user_confirmation`（实际用户确认，必须记录内容）。存在正式剖视证据时可省略此字段；不能把无剖面线的外观图随意称为剖视，也不能编造用户确认。视图之间仍有矛盾时应先解决，不能用“估计尺寸”代替空腔类型的确认。

`check-stl` 读取 NX 导出的毫米制 ASCII 或二进制 STL，执行案例中的检查。带历史要求的案例必须同时传入 `--history`；STL 哈希要与历史记录匹配，避免拿错网格。退出码 `0` 为所列检查通过，`1` 为读图证据或几何检查未通过，`2` 为输入/运行错误。

### 从 NX 导出临时校验数据

在安装 NX 的 Windows 中运行（先使用新的输出文件名）：

```powershell
& 'C:\Program Files\Siemens\NX2007\NXBIN\run_journal.exe' `
  'nx\export_for_check.py' -args '零件.prt' 'work\part-2.stl'
```

日志同时生成 `.stl.history.json`，记录原零件哈希、网格哈希、单位、实体数量和原生特征列表。该日志只打开并导出，不保存输入零件。已在 NX 2007 实机环境验证。`preview` 输出正投影及指定平面的网格截线，用于并排核对原图；它不是 NX 工程制图，遮挡与着色不能代替实体校验。

## 检查种类

| 检查 | 用途 |
| --- | --- |
| `clear_line` | 线段不得穿过任何实体表面，发现贯通孔里残留的底板 |
| `solid_line` | 线段至少穿过两个表面，检查切孔后连接筋和轮毂仍存在 |
| `clear_points` | 指定点必须位于实体外 |
| `clear_spherical_cap` | 在指定球面内腔中布置点，查找伸入材料 |
| `inner_sphere_surface` | 从内腔向外探测，检查第一处内壁是否落在指定球面上 |

案例坐标使用现有模型的建模基准：零件 2 左端孔中心为 XY 原点；零件 3 球盖底面为 Z=0，球心为 `(0,0,-36)`。不同模型必须重新设置坐标、测试位置和单位，不能直接套用。

网格应来自封闭、有效的实体，且必须使用与案例一致的单位。网格采样只验证指定位置，不能替代所有尺寸、制造公差和完整表面检验。内球面检查避开接管开口；真正的开口处不应强行要求存在球面。

## NX 工作流程

1. 读取原始嵌入图像，逐个核对正投影、剖视（如有）和轴测图。
2. 为每个重要特征记录材料/空腔、贯通/盲孔、尺寸来源及对应视图。空腔深度要记录剖视、隐藏轮廓或明确标注的依据；原图仍不确定时向用户确认。
3. 根据特征表安排 NX 草图与增减材操作。每次去除材料建立可编辑的独立特征；保留有意义的名称和建模历史。
4. 将模型转到原图方向，核对正视、俯视、侧视；执行穿过关键结构的剖切。
5. 临时导出 STL，执行贯通、连接筋和内腔检查；检查失败时返回原图和特征历史定位问题。
6. 重新打开最终 `.prt`，核对实体和历史，并清除临时图像、网格和日志。最终 NX 作业目录仅保留 `.prt` 和必要的 `.md`。

## 项目选择

已调查 [eDOCr2](https://github.com/javvi51/edocr2) 和 [2D-to-3D CAD Reconstruction](https://github.com/Mohil-Ahuja/2D-to-3D-CAD-Reconstruction)。前者处理机械图的分割及 OCR，后者主要使用合成三视图和限定零件模板。此次错误集中于材料/空腔判断与建模后的内部结构验证，因此采用自开发的证据记录和几何检查流程。后续尺寸文字识别需要增强时，可再接入专用 OCR。

## 可复用的 Codex 技能

[SKILL.md](SKILL.md) 包含下次读图和建模时的执行要求，可将本项目目录链接到 `~/.codex/skills/nx-drawing-checker`，由后续会话发现。安装 Python 包后也可直接使用命令行，技能没有改变模型本身或训练基础模型。

## 验证

```bash
python -m unittest discover -s tests -v
```

测试包含：原图字节保持和文档顺序、非法裁剪、缺少剖视依据的拒绝、贯通空间的错误底板检测、内腔中的多余实体检测，以及 ASCII/二进制 STL 读取。

本次实机结果和修订内容见 [VALIDATION.md](VALIDATION.md)，详细检查见 [reports/part-2.md](reports/part-2.md) 与 [reports/part-3.md](reports/part-3.md)。未标尺寸、全部制造公差和未采样区域仍需单独核对。

## 参与与许可

欢迎使用中文或英文提交可复现问题与改进，见 [CONTRIBUTING.md](CONTRIBUTING.md)。
维护方向见 [ROADMAP.md](ROADMAP.md)。项目处于早期阶段，路线图不代表已完成功能。
代码采用 [MIT 许可证](LICENSE)。Siemens NX 是独立的专有软件，本项目不隶属于 Siemens，也未获得其背书。
