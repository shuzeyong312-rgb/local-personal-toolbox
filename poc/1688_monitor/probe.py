"""Read existing Chrome only. No launch, navigation, requests or browser close."""
import argparse
import json
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
PATTERN = r'https://detail\.1688\.com/offer/\d+\.html(?:\?.*)?'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.url and not re.fullmatch(PATTERN, args.url):
        parser.error('Expected an HTTPS 1688 product detail URL')
    output = {'success': False, 'cdp_connected': False}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp('http://127.0.0.1:9222', timeout=5000)
            output['cdp_connected'] = True
            pages = [p for c in browser.contexts for p in c.pages if re.fullmatch(PATTERN, p.url)]
            if args.url:
                pages = [p for p in pages if p.url.split('?')[0] == args.url.split('?')[0]]
            if len(pages) != 1:
                raise RuntimeError(f'Found {len(pages)} product tabs; use --url to select exactly one')
            page = pages[0]
            page.wait_for_load_state('domcontentloaded', timeout=10000)
            print('[page] existing tab loaded', file=sys.stderr)
            runs = []
            for index in range(3):
                result = page.evaluate((ROOT / 'extract.js').read_text(encoding='utf-8'))
                result['url'] = page.url.split('?')[0]
                result['offer_id'] = re.search(r'/offer/(\d+)', page.url).group(1)
                runs.append(result)
                print(f'[run {index+1}] assistant: {result["assistant_detected"]}', file=sys.stderr)
                for section in ['product', 'assistant']:
                    for key, value in result[section].items():
                        print(f'[field] {section}.{key}: {value}', file=sys.stderr)
                for key, reason in result['unavailable_reasons'].items():
                    print(f'[unavailable] {key}: {reason}', file=sys.stderr)
                for sku_index, sku in enumerate(result['skus']):
                    for key, value in sku.items():
                        if value != 'unavailable':
                            print(f'[field] skus[{sku_index}].{key}: {value}', file=sys.stderr)
                if index < 2:
                    time.sleep(2)
            output.update(success=bool(runs[0]['assistant_detected'] and runs[0]['product']['title'] != 'unavailable'),
                          runs=runs, three_reads_identical=runs[0] == runs[1] == runs[2], read_interval_seconds=2)
            if args.debug:
                debug = ROOT / 'debug'
                debug.mkdir(exist_ok=True)
                fragment = page.evaluate("() => Array.from(document.querySelectorAll('.goods-operation-label,.price-component,.expand-view-item,h1')).map(e=>e.parentElement.outerHTML.slice(0,12000)).slice(0,8).join('\\n')")
                (debug / 'current_fragments.html').write_text(fragment, encoding='utf-8')
    except Exception as exc:
        output['error'] = str(exc)
        print('[page] failed', file=sys.stderr)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if 'runs' in output else 1


if __name__ == '__main__':
    raise SystemExit(main())
