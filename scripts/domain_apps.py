#!/usr/bin/env python3
"""Look up Appfigures catalog apps associated with a domain.

Uses the Appfigures CLI Explorer API and verifies exact domain/subdomain matches
in URL/contact fields locally.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from urllib.parse import urlparse

GENERIC_DOMAINS = {
    'gmail.com', 'googlemail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
    'live.com', 'msn.com', 'icloud.com', 'me.com', 'mac.com', 'aol.com',
    'proton.me', 'protonmail.com', 'pm.me', 'mail.com', 'gmx.com', 'gmx.de',
    'web.de', 'qq.com', '163.com', '126.com', 'inbox.ru', 'yandex.com',
    'yandex.ru', 'hey.com', 'fastmail.com', 'zoho.com', 'yahoo.fr',
    'gmaill.com', 'gmial.com', 'gamil.com', 'gnail.com', 'hotmial.com',
    'outlok.com', 'yaho.com', 'gmil.com'
}
DISPOSABLE_HINTS = (
    'mailinator', 'tempmail', '10minutemail', 'guerrillamail', 'emailax',
    'sharklasers', 'yopmail', 'throwaway', 'dispostable'
)
CATALOG_URL_FIELDS = ['support_url', 'developer_site', 'developer_email', 'view_url']
FIELDS = ','.join([
    'product_id',
    'name',
    'developer',
    'storefronts',
    'developer_site',
    'developer_email',
    'support_url',
    'view_url',
    'custom_meta[country=zz].download_estimates_sum_30_days',
    'custom_meta[country=zz].revenue_estimates_sum_30_days',
])


def normalize_domain(value: str) -> str:
    s = (value or '').strip().lower().strip('.')
    if '@' in s and not s.startswith(('http://', 'https://')):
        s = s.rsplit('@', 1)[1]
    if '/' in s or ':' in s:
        parsed = urlparse(s if '://' in s else 'https://' + s)
        s = parsed.hostname or s
    if s.startswith('www.'):
        s = s[4:]
    return s.strip().strip('.')


def valid_domain(domain: str, allow_generic: bool = False) -> tuple[bool, str | None]:
    if not domain:
        return False, 'empty domain'
    if not allow_generic and domain in GENERIC_DOMAINS:
        return False, 'generic/free email domain'
    if any(h in domain for h in DISPOSABLE_HINTS):
        return False, 'disposable-looking domain'
    if domain.count('.') < 1 or len(domain) > 80:
        return False, 'invalid domain shape'
    if not re.match(r'^[a-z0-9.-]+\.[a-z]{2,}$', domain):
        return False, 'invalid domain characters'
    stem = domain.split('.')[0]
    if len(stem) < 3:
        return False, 'domain stem too short'
    return True, None


def value_matches_domain(value: str | None, domain: str) -> bool:
    if not value:
        return False
    s = str(value).strip().lower()
    if s.startswith('mailto:'):
        host = s.split(':', 1)[1].split('@')[-1].split('?')[0].strip()
    elif '@' in s and not s.startswith(('http://', 'https://')):
        host = s.split('@')[-1].split('?')[0].strip()
    else:
        parsed = urlparse(s if '://' in s else 'https://' + s)
        host = (parsed.hostname or '').lower()
    host = host.strip('.').removeprefix('www.')
    return host == domain or host.endswith('.' + domain)


def row_metric(row: dict, key: str) -> int:
    # Newer Appfigures CLI can return filtered nested fields either as
    # custom_meta rows or as flattened keys, depending on version.
    flat_key = f'custom_meta[country=zz].{key}'
    v = row.get(flat_key)
    if isinstance(v, (int, float)):
        return int(v)
    for cm in row.get('custom_meta') or []:
        if not isinstance(cm, dict) or not isinstance(cm.get(key), (int, float)):
            continue
        if cm.get('country') == 'zz':
            return int(cm[key])
    v = row.get(key)
    return int(v) if isinstance(v, (int, float)) else 0


def explorer_query(raw: str, count: int) -> list[dict]:
    query = json.dumps(['raw', raw])
    cmd = ['appfigures', 'explorer', 'query', query, '--extra-fields', FIELDS, '--count', str(count)]
    cp = subprocess.run(cmd, text=True, capture_output=True, timeout=120)
    if cp.returncode != 0:
        raise RuntimeError((cp.stderr or cp.stdout or '').strip())
    payload = json.loads(cp.stdout)
    return payload.get('results') or []


def catalog_query(domain: str, count: int) -> list[dict]:
    by_id: dict[int, dict] = {}
    for field in CATALOG_URL_FIELDS:
        raw = f'{field}:"{domain}" OR {field}:"www.{domain}"'
        for row in explorer_query(raw, count):
            product_id = row.get('product_id')
            if product_id is None:
                continue
            existing = by_id.setdefault(product_id, row)
            matched = set(existing.get('_matched_url_fields') or [])
            if value_matches_domain(row.get(field), domain):
                matched.add(field)
            existing['_matched_url_fields'] = sorted(matched)

    verified = []
    for row in by_id.values():
        matched = [f for f in CATALOG_URL_FIELDS if value_matches_domain(row.get(f), domain)]
        if matched:
            row['_matched_url_fields'] = matched
            verified.append(row)
    return verified


def compact_app(row: dict) -> dict:
    return {
        'product_id': row.get('product_id'),
        'name': row.get('name'),
        'developer': row.get('developer'),
        'storefronts': row.get('storefronts') or [],
        'matched_url_fields': row.get('_matched_url_fields') or [],
        'downloads_30d': row_metric(row, 'download_estimates_sum_30_days'),
        'revenue_30d_net_usd': row_metric(row, 'revenue_estimates_sum_30_days'),
        'developer_site': row.get('developer_site'),
        'developer_email': row.get('developer_email'),
        'support_url': row.get('support_url'),
        'view_url': row.get('view_url'),
    }


def print_table(domain: str, apps: list[dict]) -> None:
    total_downloads = sum(a['downloads_30d'] or 0 for a in apps)
    total_revenue = sum(a['revenue_30d_net_usd'] or 0 for a in apps)
    print(f'domain={domain} apps={len(apps)} downloads_30d={total_downloads:,} revenue_30d_net_usd=${total_revenue:,.0f}')
    if not apps:
        print('No exact domain/subdomain matches found.')
        return
    for app in sorted(apps, key=lambda a: ((a['revenue_30d_net_usd'] or 0), (a['downloads_30d'] or 0)), reverse=True):
        stores = ','.join(str(s) for s in app['storefronts'])
        matched = ','.join(app['matched_url_fields'])
        print(f"\n{app['product_id']}  {app['name']}  [{stores}]")
        print(f"  developer: {app['developer']}")
        print(f"  matched: {matched}")
        print(f"  downloads_30d: {app['downloads_30d']:,}  revenue_30d_net_usd: ${app['revenue_30d_net_usd']:,.0f}")
        for field in CATALOG_URL_FIELDS:
            if app.get(field):
                print(f"  {field}: {app[field]}")


def main() -> int:
    ap = argparse.ArgumentParser(description='Turn a domain into matching Appfigures catalog apps.')
    ap.add_argument('domain', help='Domain, URL, or email address')
    ap.add_argument('--count', type=int, default=100, help='Explorer result count per field')
    ap.add_argument('--allow-generic', action='store_true', help='Allow generic email domains like gmail.com')
    ap.add_argument('--format', choices=['table', 'json'], default='table')
    args = ap.parse_args()

    domain = normalize_domain(args.domain)
    ok, reason = valid_domain(domain, args.allow_generic)
    if not ok:
        payload = {'domain': domain, 'error': reason, 'apps': [], 'app_count': 0}
        if args.format == 'json':
            print(json.dumps(payload, indent=2))
        else:
            print(f'domain={domain} error={reason}')
        return 2

    rows = catalog_query(domain, args.count)
    apps = [compact_app(r) for r in rows]
    total_downloads = sum(a['downloads_30d'] or 0 for a in apps)
    total_revenue = sum(a['revenue_30d_net_usd'] or 0 for a in apps)
    payload = {
        'domain': domain,
        'app_count': len(apps),
        'total_downloads_30d': total_downloads,
        'total_revenue_30d_net_usd': total_revenue,
        'matched_by': CATALOG_URL_FIELDS,
        'apps': sorted(apps, key=lambda a: ((a['revenue_30d_net_usd'] or 0), (a['downloads_30d'] or 0)), reverse=True),
    }
    if args.format == 'json':
        print(json.dumps(payload, indent=2))
    else:
        print_table(domain, payload['apps'])
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        raise SystemExit(1)
