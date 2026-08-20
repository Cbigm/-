# Amazon 词库自动搭建应用

一个用于亚马逊关键词运营的小工具：

- 上传竞品/工具流量词表（CSV/XLSX）
- 输入产品参数特性描述
- 输入产品图片提炼标签
- 自动生成「可投放词库」并给出意图分类与建议投放位

## 启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 输入建议

1. 词表至少包含一列关键词。
2. 如果有搜索量列，选择后会参与评分。
3. 产品卖点建议包含材质、功能、场景、人群。
4. 图片标签建议包含使用场景、外观风格、核心差异。

## 输出字段

- `keyword`: 候选词
- `source`: 来源（流量表 / 产品参数卖点 / 产品图片）
- `frequency`: 命中次数
- `intent`: 搜索意图（购买 / 信息 / 品牌 / 泛搜索）
- `score`: 综合评分
- `recommended_slot`: 建议埋词位置（Title/Bullet/A+/Search Term）
