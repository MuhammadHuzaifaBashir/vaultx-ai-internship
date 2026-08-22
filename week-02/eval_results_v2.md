# Task 05 - Evaluation Results (v2)

## Accuracy

- **category**: 100.0%
- **priority**: 75.0%
- **sentiment**: 83.3%
- **needs_human**: 91.7%

## Per-Case Results

| Message | Expected | Actual | Correct |
|---|---|---|---|
| I've been charged twice for my subscription this m | ('billing', 'high', 'negative', True) | ('billing', 'urgent', 'negative', True) | No |
| How do I reset my password? | ('account', 'low', 'neutral', False) | ('account', 'low', 'neutral', False) | Yes |
| Your app keeps crashing every time I try to upload | ('technical', 'high', 'negative', True) | ('technical', 'medium', 'neutral', False) | No |
| Can you tell me what plans you offer? | ('general', 'low', 'neutral', False) | ('general', 'low', 'neutral', False) | Yes |
| This is the third time I've contacted support abou | ('technical', 'high', 'negative', True) | ('technical', 'high', 'negative', True) | Yes |
| Just wanted to say thanks, your support team fixed | ('general', 'low', 'positive', False) | ('general', 'low', 'positive', False) | Yes |
| I need to update my billing address. | ('billing', 'low', 'neutral', False) | ('billing', 'low', 'neutral', False) | Yes |
| The website is down for me, is there an outage? | ('technical', 'high', 'neutral', False) | ('technical', 'high', 'neutral', False) | Yes |
| I think I was overcharged, can someone check my in | ('billing', 'medium', 'neutral', True) | ('billing', 'medium', 'neutral', True) | Yes |
| My account got locked after I tried logging in fro | ('account', 'high', 'negative', True) | ('account', 'high', 'neutral', True) | No |
| This is unacceptable, I want a full refund immedia | ('billing', 'high', 'negative', True) | ('billing', 'urgent', 'negative', True) | No |
| I suspect someone accessed my account without perm | ('account', 'urgent', 'negative', True) | ('account', 'urgent', 'negative', True) | Yes |