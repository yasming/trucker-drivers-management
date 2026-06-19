# Testing guidelines

## Do NOT run ad-hoc inline scripts to "test" the API

Do not exercise the API with throwaway one-liners like:

```bash
# ❌ Don't do this
.venv/bin/python -c "
import django; django.setup()
from django.test import Client
c = Client()
print(c.get('/api/drivers/').status_code)
"
```