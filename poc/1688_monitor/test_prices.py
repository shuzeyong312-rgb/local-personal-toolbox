"""DOM regression checks via existing CDP, using one self-created local blank tab."""
from pathlib import Path
from playwright.sync_api import sync_playwright

script = Path(__file__).with_name('extract.js').read_text(encoding='utf-8')
with sync_playwright() as pw:
    browser = pw.chromium.connect_over_cdp('http://127.0.0.1:9222', timeout=5000)
    page = browser.contexts[0].new_page()
    try:
        page.set_content('''<div class="ms-container"><div class="title-content"><h1>test</h1></div>
          <div class="price-component"><div class="price-info"><span>¥</span><span>125</span><span>.00</span><span hidden>999</span></div><p>1件起批<span>60天老客价</span></p></div>
          <div class="price-component"><div class="price-info"><span>¥</span><span>117</span><span>.00</span></div><p>100-999件</p></div>
          <div class="price-component"><div class="price-info"><span>¥</span><span>110</span><span>.00</span></div><p>≥1000件</p></div>
          <div class="price-component" hidden><div class="price-info">¥1</div><p>99件起批</p></div></div>
          <div class="price-component"><div class="price-info">¥2</div><p>88件起批</p></div>''')
        result = page.evaluate(script)['product']
        assert result['price_raw_values'] == ['¥125.00', '¥117.00', '¥110.00'], result
        assert result['min_order_qty'] == '1件起批', result
        assert result['price_tiers'] == [
            {'qty_raw':'1件起批','price_raw':'¥125.00'},
            {'qty_raw':'100-999件','price_raw':'¥117.00'},
            {'qty_raw':'≥1000件','price_raw':'¥110.00'}], result
        page.set_content('''<div class="ms-container"><div class="title-content"><h1>test</h1></div>
          <div class="price-component"><div class="price-info">¥45.00</div><div class="price-info">¥50.00</div><p>1台起批<span>60天老客价</span></p></div></div>''')
        result = page.evaluate(script)['product']
        assert result['price_raw_values'] == ['¥45.00','¥50.00']
        assert result['price_tiers'] == []
        assert result['min_order_qty'] == '1台起批'
        page.set_content('<div class="ms-container"><div class="title-content"><h1>test</h1></div></div>')
        result = page.evaluate(script)['product']
        assert result['price_raw_values'] == [] and result['min_order_qty'] == 'unavailable'
    finally:
        page.close()  # Only close the local test tab created above.
print('DOM price order, hidden/outside exclusion, quantity matching and ambiguity checks passed')
