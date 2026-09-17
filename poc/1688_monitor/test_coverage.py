"""Small regression check: visible rows must not imply a selected SKU."""
from coverage import flatten, ASSISTANT_FIELDS, found

raw = {'product':{'title':'test', 'price_raw_values':['¥89.00','¥95.00'], 'min_order_qty':'5件起批', 'sales_raw':'已售900+件'},
       'assistant':dict.fromkeys(ASSISTANT_FIELDS,'10+'), 'unavailable_reasons':{},
       'skus':[{'name':'white', 'selected':False, 'price_raw':'¥89'},
               {'name':'green', 'selected':False, 'price_raw':'¥95'}],
       'assistant_detected':True, 'product_detected':True, 'dom_structure':{}, 'login_evidence_raw':[]}
result = flatten(raw, 'https://detail.1688.com/offer/123.html')
assert result['fields']['visible_sku_names'] == ['white','green']
assert result['fields']['selected_sku_price_raw'] == 'unavailable'
assert result['fields']['selected_sku_name'] == 'unavailable'
assert result['fields']['price_raw_values'] == ['¥89.00','¥95.00']
assert result['fields']['month_sales_raw'] == '10+'
assert not found([]) and not found('unavailable')
print('Coverage raw-text and unselected-SKU checks passed')
