# ECharts 图片转换器

**作者:** hangboss1761
**版本:** 0.0.1
**类型:** tool
**仓库:** <https://github.com/hangboss1761/echarts-convert-dify-plugin>

## 概述

ECharts 图片转换器是一个强大的 Dify 插件，能够将文本中的 ECharts 配置转换为高质量的图片。该插件支持批量处理、并发渲染，以及灵活的输出格式配置。

**使用场景**: 适用于将markdown字符串中的ECharts图表配置转换为图片，然后将完整的markdown字符串转为docx/pdf等格式（使用`md_exporter`插件）。

![usecase](../_assets/image.png)

此插件完全离线运行，零外部依赖。

> Echarts 版本: 5.6.0

## 配置

ECharts 图片转换器提供以下配置选项：

### 输入参数

- **内容**: 包含 ````echarts```` 代码块的文本，代码块中包含 ECharts JSON 配置（必需）
- **图片类型**: 输出图片格式（`svg` - 仅支持 SVG）
- **宽度**: 图表宽度（像素，100-4000，默认：800）
- **高度**: 图表高度（像素，100-4000，默认：600）

### 高级选项

- **Worker 数量**: 并发渲染的工作线程数（1-4，默认：1）
  - **建议**: 复杂图表用2-4，简单图表用1
- **合并 ECharts 配置**: 附加的 ECharts 配置（JSON 格式）（可选）

### ⚡ 并发性能指南

**使用并发** (2-4线程):
- 包含大量数据集的复杂图表
- 多序列可视化
- 性能取决于您的硬件能力

**使用顺序** (不使用worker):
- 简单图表（柱状图、饼图、折线图）
- 小数据集
- 单个图表渲染

**注意**: 性能提升取决于设备规格和图表复杂度。

## 开发

### 开发环境设置

复制 `.env.example` 到 `.env` 并填写配置值。

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 js-executor 依赖（仅开发需要）
cd js-executor
# 安装 Bun: <https://bun.sh/docs/installation>
# 如果已经安装了 Bun 可以跳过
bun install

# 以开发模式运行
python -m main

# 以开发模式运行，使用 bun run build:dev 构建本地可执行文件。
ECHARTS_CONVERT_LOCAL_PATH=./executables/echarts-convert-local python -m main

# 更多信息请查看 GUIDE.md
```

**注意:** 对于 Dify 中的生产部署，插件需要**零外部依赖**。所有 JavaScript 运行时依赖都与插件捆绑，支持完全离线操作，无需任何外部 API 调用或互联网连接。

然后在 Dify 工作流中添加插件并进行测试。

## 使用示例

```markdown
# 示例图表

```echarts
{
  "title": {
    "text": "示例图表"
  },
  "xAxis": {
    "type": "category",
    "data": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
  },
  "yAxis": {
    "type": "value"
  },
  "series": [{
    "data": [120, 200, 150, 80, 70, 110, 130],
    "type": "bar"
  }]
}
```
```

插件会自动提取 ECharts 配置并将其转换为指定格式的图片。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

**注意**: 此插件专为 Dify 平台设计，需要在 Dify 环境中运行。