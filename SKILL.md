---
name: appfigures-domain-apps
description: Turn a company/email/web domain into a list of matching apps using the Appfigures CLI. Use when someone asks to find apps owned by or associated with a domain, domain-to-app lookup, catalog URL/contact matching, or “what apps are connected to this domain?”. Requires the `appfigures` CLI to be installed and authenticated.
---

# Appfigures Domain → Apps

Use this skill to look up apps associated with a domain using the Appfigures CLI. It only searches catalog URL/contact fields and then verifies exact host/subdomain matches locally.

## Quick use

```bash
python3 scripts/domain_apps.py example.com --format table
python3 scripts/domain_apps.py example.com --format json
```

If running outside the skill directory, use the absolute script path.

## What it matches

The script queries Appfigures Explorer for the domain in these fields:

- `support_url`
- `developer_site`
- `developer_email`
- `view_url`

Then it verifies locally that the parsed host is exactly the domain or a subdomain of it.

Examples:

- `example.com` matches `example.com`, `www.example.com`, `support.example.com`
- `example.com` does **not** match `notexample.com` or `example.com.evil.test`
- generic/free email domains like `gmail.com` are skipped by default

## Output

Table output includes:

- product id
- app name
- developer
- storefronts
- matched fields
- 30-day downloads estimate
- 30-day net revenue estimate
- URL/contact fields

JSON output includes the same data plus totals.

## Notes

- This is a catalog-domain lookup, not proof of legal ownership.
- Do not match by app name or developer name unless explicitly asked; the safe default is URL/contact fields only.
- If the CLI returns no results, report “no exact domain/subdomain matches found.”
