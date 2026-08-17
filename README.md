# 一批销售成长

面向服装一批档口老板/主理人、店长和批发销售的每日短分享网站。内容服务于全国批发客户、连锁客户、电商客户、服装店老板娘和买手等拿货人群。

- 每天北京时间 14:00 固定更新 8 条，每个分类 1 条
- 分类为销售认知、批发技巧、客户经营、执行心态、服务履约、团队协作、店长管理、销售复盘
- 聚焦开发拿货客户、看版选款、组货报价、起批、补单返单、动销反馈、发货库存和订货会
- 校验器会拒绝顾客进店、试穿推荐等零售化场景
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

当日输入 JSON 是包含正好 8 个对象的数组，每个对象包含：
`category`、`audience`、`title`、`content`、`example`、`action`。

内容规范：标题8—16字；正文70—115字、3—5个短句；档口表达20—45字；今日行动15—32字；四字段合计150—220字。没有“晚上复盘”字段。
