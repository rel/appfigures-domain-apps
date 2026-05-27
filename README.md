# Appfigures Domain Apps Skill

An OpenClaw/agent skill that turns a domain into a best-guess list of apps using the [Appfigures CLI on npm](https://www.npmjs.com/package/appfigures).

It searches Appfigures catalog URL/contact fields, then verifies exact domain/subdomain matches locally.

## Requirements

- [Appfigures CLI](https://www.npmjs.com/package/appfigures) installed and authenticated
- Python 3.10+

## Usage

```bash
python3 scripts/domain_apps.py focustown.app --format table
python3 scripts/domain_apps.py focustown.app --format json
```

## What it matches

The lookup searches these catalog fields:

- `support_url`
- `developer_site`
- `developer_email`
- `view_url`

Then it verifies that the parsed host is exactly the domain or a subdomain of it.

For example, `example.com` matches `example.com`, `www.example.com`, and `support.example.com`, but not `notexample.com` or `example.com.evil.test`.

## Common domains

The skill ignores common/generic email domains by default, including domains like `gmail.com`, `yahoo.com`, `hotmail.com`, `outlook.com`, and `icloud.com`.

If you really need to query one of those domains, pass:

```bash
python3 scripts/domain_apps.py gmail.com --allow-generic
```

## Output

The script returns matching apps with:

- product id
- app name
- developer
- storefronts
- matched URL/contact fields
- 30-day downloads estimate
- 30-day net revenue estimate

## Notes

This is a best guess based on domains associated with apps in the Appfigures catalog. It is useful for finding likely apps connected to a company/domain, but it is not proof of legal ownership or control.
