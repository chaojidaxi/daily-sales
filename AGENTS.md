# Daily Sales project rules

This repository powers the public Chinese website “每日销售成长”.

## Daily content requirements
- Publish at least 5 items for the current Asia/Shanghai date.
- Cover all five categories exactly or at least once: 销售认知、实战技巧、客户经营、执行心态、团队管理.
- Audience must be one of 老板、店长、销售、全员、老板/店长、店长/销售.
- Each item: a practical title, 3–5 short Chinese sentences (45–180 Chinese characters total), and one executable action (12–60 characters).
- Be professional, direct, operational, and suitable for fashion retail/wholesale training clients.
- Avoid empty motivational slogans, fabricated figures, punitive/fine-based management, contact details, and off-platform promotion.
- Do not modify the separate `daily-copy` repository.

## Verification
Run both before committing:

```bash
python3 scripts/update_data.py --check
python3 -m unittest discover -s tests -v
```
