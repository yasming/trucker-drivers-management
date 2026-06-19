# Testing guidelines

## Frontend: batch edits, test once

Do NOT run `npm run build` after every small change. TypeScript compilation is slow.
Instead:
- Make multiple related changes to components/styles/types
- Run type-check + build **once** when the batch is complete
- Fix all errors together

This applies to any repetitive `npm run` or `.venv/bin/python manage.py test` loop.

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