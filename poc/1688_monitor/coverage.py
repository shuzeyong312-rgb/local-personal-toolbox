"""Coverage POC for explicitly supplied URLs; no search or SKU interaction."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
PRODUCT_FIELDS = ['offer_id', 'title', 'price_raw_values', 'min_order_qty', 'sales_raw',
                  'visible_sku_names', 'selected_sku_name', 'selected_sku_price_raw',
                  'selected_sku_availability', 'selected_sku_stock_raw']
ASSISTANT_FIELDS = ['listed_at', 'month_sales_raw', 'month_distribution_raw',
                    'year_sales_quantity_raw', 'year_sales_orders_raw',
                    'review_count_raw', 'positive_rate_raw']
FIELDS = PRODUCT_FIELDS + ASSISTANT_FIELDS


def found(value):
    return bool(value) and value != 'unavailable'


def wait_product(page, script, timeout=10, clock=time.monotonic, pause=time.sleep):
    start = clock()
    previous = None
    observations = []
    while clock() - start < timeout:
        raw = page.evaluate(script)
        state = {'title': raw['product']['title'], 'region': raw['product_detected'],
                 'structure': raw['dom_structure']}
        observations.append(state)
        structure = state['structure']
        ready = state['region'] and state['title'] not in ('', 'unavailable') and (
            structure['price_value_count'] > 0 or structure['color_button_count'] > 0 or
            structure['visible_spec_row_count'] > 0)
        if ready and state == previous:
            return {'stable': True, 'seconds': round(clock() - start, 3), 'observations': observations}
        previous = state
        pause(min(0.5, max(0, timeout - (clock() - start))))
    return {'stable': False, 'seconds': round(clock() - start, 3), 'observations': observations}


def flatten(raw, url):
    fields = {key: raw['product'][key] for key in PRODUCT_FIELDS[1:5]}
    fields['offer_id'] = re.search(r'/offer/(\d+)', url).group(1)
    fields.update({key: raw['assistant'][key] for key in ASSISTANT_FIELDS})
    reasons = {key: raw['unavailable_reasons'].get('product.' + key,
               raw['unavailable_reasons'].get('assistant.' + key, '未展示或结构不唯一')) for key in fields}
    names = [sku['name'] for sku in raw['skus'] if sku['name'] != 'unavailable']
    fields['visible_sku_names'] = names or 'unavailable'
    selected = [(i, sku) for i, sku in enumerate(raw['skus']) if sku['selected']]
    mappings = {'selected_sku_name': 'specification_raw', 'selected_sku_price_raw': 'price_raw',
                'selected_sku_availability': 'availability', 'selected_sku_stock_raw': 'stock_raw'}
    for key, source in mappings.items():
        fields[key] = selected[0][1][source] if len(selected) == 1 else 'unavailable'
        reasons[key] = raw['unavailable_reasons'].get(f'skus[{selected[0][0]}].{source}',
                       '当前颜色/规格行无法唯一对应') if len(selected) == 1 else '当前颜色/规格行无法唯一对应'
    reasons['visible_sku_names'] = '未找到支持结构的可见颜色按钮'
    return {'fields': fields, 'price_tiers':raw['product'].get('price_tiers',[]),
            'unavailable_reasons': {k: reasons[k] for k, v in fields.items() if not found(v)},
            'assistant_detected': raw['assistant_detected'],
            'product_detected': raw['product_detected'], 'dom_structure':raw['dom_structure'],
            'page_metadata':raw.get('page_metadata',{}),
            'login_evidence_raw': raw['login_evidence_raw']}


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' / ')


def report(results):
    n = len(results)
    completed = n == 10 and all(len(r['reads']) == 3 for r in results)
    lines = ['# 10 商品跨商品覆盖率 POC', '',
             f'状态：{"完成10商品读取" if completed else "未完成，等待样本"}。当前实际样本 {n}/10；未提供样本不算字段失败。', '',
             '复用现有 Chrome CDP http://127.0.0.1:9222 和现有采集器；只读取DOM，不搜索、不遍历SKU，不接数据库/UI/定时任务。', '',
             '成功数：该商品三次均取得非 unavailable 值；一致数：三次值相同。缺失值一致不算获取成功。当前SKU名称列记录已选规格原文，颜色名称见可见列表。', '',
             '## 商品概况与稳定等待', '',
             '商品区最多等待10秒，每0.5秒检查真实DOM：标题、商品区域和价格/SKU节点出现且连续两次状态相同才开始正式三读。空区域相同不能判为稳定，超时不补值。助手仍按原方式读取；两次就绪状态不保证全部异步数据已完成。', '',
             '| 商品 | 店铺原文 | 类目原文 | 等待稳定 / 秒 | 商品区三次识别 | 助手三次识别 |',
             '| --- | --- | --- | --- | --- | --- |']
    for r in results:
        first = r['reads'][0] if r['reads'] else {}
        metadata = first.get('page_metadata', {})
        wait = r.get('product_wait', {})
        lines.append('| ' + ' | '.join(cell(v) for v in [r['url'], metadata.get('merchant_raw','unavailable'),
            metadata.get('category_raw','unavailable'), str(wait.get('stable'))+' / '+str(wait.get('seconds')),
            [x['product_detected'] for x in r['reads']], [x['assistant_detected'] for x in r['reads']]])+' |')
    lines += ['', '## 字段覆盖率', '', '| 字段 | 成功/已测试 | 三次一致/已测试 | 缺失原因（次数为商品数） |', '| --- | --- | --- | --- |']
    for field in FIELDS:
        success = sum(len(r['reads']) == 3 and all(found(x['fields'][field]) for x in r['reads']) for r in results)
        consistent = sum(len(r['reads']) == 3 and all(x['fields'][field] == r['reads'][0]['fields'][field] for x in r['reads']) for r in results)
        reasons = Counter(reason for r in results for reason in set(x['unavailable_reasons'].get(field) for x in r['reads']) if reason)
        lines.append(f'| {field} | {success}/{n} | {consistent}/{n} | {cell(dict(reasons))} |')
    for r in results:
        lines += ['', f'## 商品 {r["url"]}', '', f'读取错误：{cell(r.get("error", "无"))}', '',
                  '| 字段 | 第1次 | 第2次 | 第3次 |', '| --- | --- | --- | --- |']
        for field in FIELDS:
            values = [cell(x['fields'][field]) for x in r['reads']]
            values += ['未执行'] * (3 - len(values))
            lines.append('| ' + field + ' | ' + ' | '.join(values) + ' |')
        if r['reads']:
            first=r['reads'][0]
            lines += ['', f'商品区域识别：{first["product_detected"]}；助手识别：{first["assistant_detected"]}。',
                      f'DOM结构：{cell(first["dom_structure"])}；三次结构一致：{all(x["dom_structure"]==first["dom_structure"] for x in r["reads"])}。',
                      '缺失原因：'+cell(first['unavailable_reasons']),
                      '可明确对应的价格阶梯（非必有）：'+cell(first['price_tiers'])]
    lines += ['', '## 跨商品差异和 V1 判断', '',
              '样本不足10个时，不对跨商品差异、跨店铺/品类覆盖率或正式V1可行性下结论。',
              '当前采集器只读取确认的主采购区域中可见价格组件，按DOM展示顺序输出price_raw_values列表；不挑选主价或最低价。只有同组件唯一价格与明确数量文本才能生成price_tiers。起批量从价格局部可见文本匹配，不要求纯叶节点。无默认选中、多规格行时，当前SKU字段返回unavailable。',
              'available仅代表当前数量输入和加号控件可用，不能保证真实下单或库存。三次读取间隔2秒，不证明刷新或重启稳定。',
              'V1候选的最终取舍须依据覆盖率和缺失来源判断；当前规格、价格、库存、控件可用状态不能要求每个商品都有值。',
              '本阶段不采集完整SKU组合，现货率不以揽收率代替；本轮结束后不自动开发V1。', '']
    (ROOT / 'POC_10_PRODUCTS_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', action='append', required=True)
    parser.add_argument('--partial', action='store_true', help='Explicitly generate an incomplete report')
    args = parser.parse_args()
    urls = list(dict.fromkeys(u.split('?')[0] for u in args.url))
    if any(not re.fullmatch(r'https://detail\.1688\.com/offer/\d+\.html', u) for u in urls):
        parser.error('Only HTTPS 1688 detail URLs allowed')
    if len(urls) != 10 and not args.partial:
        parser.error('Exactly 10 unique URLs required; --partial labels report incomplete')
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp('http://127.0.0.1:9222', timeout=5000)
        context = browser.contexts[0]
        script = (ROOT / 'extract.js').read_text(encoding='utf-8')
        for url in urls:
            result = {'url': url, 'reads': []}
            try:
                pages = [p for p in context.pages if p.url.split('?')[0] == url]
                if len(pages) > 1:
                    raise RuntimeError('同商品有多个标签页，无法明确选择')
                page = pages[0] if pages else context.new_page()
                if not pages:
                    response = page.goto(url, wait_until='domcontentloaded', timeout=45000)
                    print(f'[page] HTTP {response.status if response else "unavailable"}', file=sys.stderr)
                page.wait_for_load_state('domcontentloaded', timeout=10000)
                try:
                    page.get_by_text('1688官方采购助手', exact=True).wait_for(state='visible', timeout=15000)
                except Exception:
                    print('[assistant] not visible within 15s; record actual DOM', file=sys.stderr)
                result['product_wait'] = wait_product(page, script)
                print(f'[wait] {url}: {result["product_wait"]["stable"]}', file=sys.stderr)
                for index in range(3):
                    result['reads'].append(flatten(page.evaluate(script), url))
                    print(f'[read] {url} {index+1}/3', file=sys.stderr)
                    if index < 2:
                        time.sleep(2)
                result['diagnostic_text'] = page.locator('.ms-container').all_inner_texts()
            except Exception as exc:
                result['error'] = str(exc)
            results.append(result)
    debug = ROOT / 'debug'
    debug.mkdir(exist_ok=True)
    (debug / 'coverage_reads.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    report(results)
    print(json.dumps({'tested_samples':len(results), 'complete':len(results)==10 and all(len(r['reads'])==3 for r in results)},ensure_ascii=False))


if __name__ == '__main__':
    main()
