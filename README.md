# 每日销售成长

面向服装老板、店长和销售团队的每日短内容网站。

- 每天北京时间 14:00 更新不少于 5 条
- 覆盖销售认知、实战技巧、客户经营、执行心态、团队管理
- 支持日期、分类、搜索和一键复制
- GitHub Pages 静态发布，数据保存在 `data.json`

## 本地检查

```bash
python3 scripts/update_data.py --check
python3 -m unittest discover -s tests -v
python3 -m http.server 8000
```

## 发布当日内容

```bash
python3 scripts/update_data.py --input /path/to/today.json --date YYYY-MM-DD
# 生成失败时使用尚未发布的备用组
python3 scripts/update_data.py --from-bank --date YYYY-MM-DD
```

当日输入 JSON 是包含至少 5 个对象的数组，每个对象包含：
`category`、`audience`、`title`、`content`、`action`。
