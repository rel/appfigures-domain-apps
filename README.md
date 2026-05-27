# Appfigures Domain Apps Skill

An OpenClaw/agent skill that turns a domain into a list of apps using the Appfigures CLI.

It searches Appfigures catalog URL/contact fields and verifies exact domain/subdomain matches locally.

## Requirements

-  CLI installed and authenticated
- Python 3.10+

## Usage



## What it matches

The lookup searches these catalog fields:

- 
- 
- 
- 

Then it verifies that the parsed host is exactly the domain or a subdomain of it.

For example,  matches , , and , but not .

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

This is a catalog-domain lookup, not proof of legal ownership.
