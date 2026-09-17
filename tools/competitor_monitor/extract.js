() => {
  const visible = e => e && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
  const text = e => visible(e) ? (e.innerText ?? e.textContent ?? '').trim() : 'unavailable';
  const direct = e => Array.from(e.childNodes).filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim();
  const nodes = Array.from(document.querySelectorAll('body *'));
  const header = nodes.find(e=>visible(e) && direct(e)==='1688官方采购助手');
  const strip = nodes.find(e=>visible(e) && direct(e)==='商品' &&
    Array.from(e.parentElement.children).some(n=>direct(n)==='月成交'))?.parentElement;
  let scope = header;
  while (scope && strip && !scope.contains(strip)) scope=scope.parentElement;
  const assistant_detected = Boolean(header && strip && scope && scope!==document.body);
  const reasons = {};
  const missing = (key, reason) => {reasons[key]=reason; return 'unavailable';};
  const assistant = {};
  const labels = {listed_at:'上架时间',month_sales_raw:'月成交',month_distribution_raw:'月代销',
    year_sales_quantity_raw:'年成交件数',year_sales_orders_raw:'年成交笔数',review_count_raw:'评论数',
    positive_rate_raw:'好评率',stock_rate_raw:'现货率'};
  for (const [key,label] of Object.entries(labels)) {
    const matches=assistant_detected ? Array.from(strip.children).filter(e=>visible(e) && direct(e)===label) : [];
    const values=matches.length===1 ? Array.from(matches[0].children).filter(visible).map(text) : [];
    assistant[key]=values.length===1 && values[0] && !['*','-','--'].includes(values[0]) ? values[0] :
      missing('assistant.'+key,'助手栏未找到唯一可见标签值：'+label);
  }
  const headings=Array.from(document.querySelectorAll('.title-content h1')).filter(visible);
  let productScope=headings.length===1 ? headings[0].closest('.ms-container') : null;
  const priceComponents=productScope ? Array.from(productScope.querySelectorAll('.price-component')).filter(visible) : [];
  const infos=priceComponents.flatMap(e=>Array.from(e.querySelectorAll('.price-info')).filter(visible));
  const priceText=e=>Array.from(e.children).filter(visible).map(text).join('') || text(e);
  const priceRawValues=infos.map(priceText).filter(value=>/^[¥￥]\s*\d/.test(value));
  const priceTiers=[];
  for(const component of priceComponents) {
    const values=Array.from(component.querySelectorAll('.price-info')).filter(visible);
    const quantityNodes=Array.from(component.querySelectorAll('p')).filter(visible);
    if(values.length===1 && quantityNodes.length===1) {
      const qty=direct(quantityNodes[0]);
      if(/^(?:\d+(?:\s*[-～~]\s*\d+)?|[≥>]\s*\d+)\s*(?:件|台|个|套|只|盒|箱|包|支|条|瓶|枚|对|本)(?:\s*起批)?$/.test(qty))
        priceTiers.push({qty_raw:qty,price_raw:priceText(values[0])});
    }
  }
  if(!priceRawValues.length) missing('product.price_raw_values','主采购价格组件没有明确可见价格，返回空列表');
  const product={title:headings.length===1 ? text(headings[0]) : missing('product.title','可见h1不唯一或不存在'),
    price_raw_values:priceRawValues,price_tiers:priceTiers,
    min_order_qty:'unavailable',sales_raw:'unavailable'};
  const minimums=[...new Set(priceComponents.flatMap(e=>
    Array.from(text(e).matchAll(/\d+\s*(?:件|台|个|套|只|盒|箱|包|支|条|瓶|枚|对|本)\s*起批/g),m=>m[0])))];
  const sales=[...new Set((productScope ? Array.from(productScope.querySelectorAll('*')).filter(visible) : [])
    .map(text)
    .map(t=>t.replace(/\s+/g,''))
    .filter(t=>/^已售(?:<|＜)?\d+(?:\.\d+)?(?:万|千)?\+?(?:件|台|个|套|只|盒|箱|包|支|条|瓶|枚|对|本)?$/.test(t)))];
  product.min_order_qty=minimums.length===1?minimums[0]:missing('product.min_order_qty','目标商品区域未找到唯一起批量');
  product.sales_raw=sales.length===1?sales[0]:missing('product.sales_raw','目标商品区域未找到唯一已售计数');
  const group=productScope ? Array.from(productScope.querySelectorAll('h3')).find(e=>text(e)==='颜色')?.closest('.feature-item') : null;
  const buttons=group ? Array.from(group.querySelectorAll('button')).filter(visible) : [];
  const rows=productScope ? Array.from(productScope.querySelectorAll('.expand-view-item')).filter(visible) : [];
  const selected=buttons.filter(e=>e.classList.contains('active'));
  const skus=buttons.map((button,i)=>{
    const current=selected.length===1 && selected[0]===button && rows.length===1;
    const row=current?rows[0]:null;
    const prices=row ? Array.from(row.querySelectorAll('.item-price-stock')).filter(e=>visible(e) && /^[¥￥]/.test(text(e))) : [];
    const input=row?.querySelector('[role="spinbutton"]');
    const plus=row?.querySelector('[aria-label="plus"]');
    const key='skus['+i+'].';
    return {name:text(button.querySelector('.label-name')),selected:Boolean(current),
      specification_raw:current?text(row.querySelector('.item-label')):missing(key+'specification_raw','未选中颜色，没有对应可见规格行'),
    price_raw:prices.length===1?text(prices[0]):missing(key+'price_raw',current?'当前SKU价格节点display:none，未当作展示值':'该颜色未展示唯一SKU价格'),
      availability:visible(input) && !input.disabled && visible(plus) && plus.classList.contains('enable') ? 'available' :
        missing(key+'availability','该颜色没有可见可用数量输入及加号控件'),
      stock_raw:current?text(row.querySelector('[i18n="sku-stock"]')):missing(key+'stock_raw','该颜色未展示库存')};
  });
  if (!buttons.length) for(const row of rows) {
    skus.push({name:text(row.querySelector('.item-label')),selected:false,
      specification_raw:'unavailable',price_raw:'unavailable',availability:'unavailable',stock_raw:'unavailable'});
  }
  if (!skus.length) missing('skus','未找到可见颜色按钮');
  const merchantHeadings=Array.from(document.querySelectorAll('h1[title]')).filter(visible);
  const category=strip ? Array.from(strip.children).find(e=>direct(e)==='类目') : null;
  return {assistant_detected,product_detected:Boolean(productScope && headings.length===1),
    page_metadata:{merchant_raw:merchantHeadings.length===1?text(merchantHeadings[0]):'unavailable',
      category_raw:category?text(category.querySelector('span')):'unavailable'},
    dom_structure:{price_value_count:infos.length,color_button_count:buttons.length,visible_spec_row_count:rows.length,selected_color_count:selected.length},
    login_state:'unavailable',
    login_evidence_raw:nodes.filter(e=>visible(e) && !e.children.length && /登录查看全部规格|登录查看更多优惠/.test(text(e))).map(text),
    product,assistant,skus,
    trend_entries:{price:scope?Array.from(scope.querySelectorAll('*')).some(e=>visible(e)&&direct(e)==='价格趋势'):false,
      sales:scope?Array.from(scope.querySelectorAll('*')).some(e=>visible(e)&&direct(e)==='销量趋势'):false},
    unavailable_fields:Object.keys(reasons),unavailable_reasons:reasons};
}
