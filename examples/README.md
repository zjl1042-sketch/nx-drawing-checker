# Reproducible synthetic demo / 可复现合成案例

After installing from the repository root:

```bash
python examples/synthetic_demo.py
```

Expected final lines include:

```text
DEMO blocked: expected=1, actual=1
DEMO clear: expected=0, actual=0
DEMO PASS: blocked clearance rejected; clear version accepted.
```

The script generates two closed box solids with a specified clear line between them.
The blocked variant adds a third closed solid crossing that line. It calls the real
`check-stl` CLI implementation and checks both exit codes. Temporary JSON and STL
files are automatically removed. NX, private drawings, and proprietary models are
not required. The demo uses multiple disconnected closed solids; it does not test
NX feature history or claim a single connected CAD body.

这是数学构造的回归演示，展示“多余材料阻挡指定贯通线 → 检出 → 移除后通过”。
视图说明是合成规格，不是真实工程图，不用于证明读图准确率或替代 NX 实机验证。
真实样本的项目记录见 [VALIDATION.md](../VALIDATION.md)。
