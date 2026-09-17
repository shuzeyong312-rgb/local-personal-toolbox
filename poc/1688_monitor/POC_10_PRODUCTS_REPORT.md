# 10 商品跨商品覆盖率 POC

状态：完成10商品读取。当前实际样本 10/10；未提供样本不算字段失败。

复用现有 Chrome CDP http://127.0.0.1:9222 和现有采集器；只读取DOM，不搜索、不遍历SKU，不接数据库/UI/定时任务。

成功数：该商品三次均取得非 unavailable 值；一致数：三次值相同。缺失值一致不算获取成功。当前SKU名称列记录已选规格原文，颜色名称见可见列表。

## 商品概况与稳定等待

商品区最多等待10秒，每0.5秒检查真实DOM：标题、商品区域和价格/SKU节点出现且连续两次状态相同才开始正式三读。空区域相同不能判为稳定，超时不补值。助手仍按原方式读取；两次就绪状态不保证全部异步数据已完成。

| 商品 | 店铺原文 | 类目原文 | 等待稳定 / 秒 | 商品区三次识别 | 助手三次识别 |
| --- | --- | --- | --- | --- | --- |
| https://detail.1688.com/offer/1056305371784.html | 广州莓有科技有限公司 | 加湿器 | True / 1.774 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/1025228589646.html | 潮州市潮安区浮洋镇桥匠电子厂 | 加湿器 | True / 1.269 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/976443859503.html | 佛山淘趣科技有限公司 | 电暖手宝 | True / 0.623 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/1045639948434.html | 佛山市相觅电器有限公司 | 电煮锅 | True / 0.69 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/1068432029920.html | 广州莓有科技有限公司 | 香薰机 | True / 0.662 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/1037232285050.html | 深圳市新智慧智芯科技有限公司 | USB风扇、迷你风扇 | True / 0.703 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/989519678078.html | 1688小店进货官方供应链 | 电煮锅 | True / 0.642 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/1062017117856.html | 东莞市乐家优品电器有限公司 | 蓝牙音箱 | True / 0.819 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/933351766381.html | 揭阳市榕城区立创电器厂 | USB风扇、迷你风扇 | True / 0.732 | [True, True, True] | [True, True, True] |
| https://detail.1688.com/offer/1018928575894.html | 深圳市质造家科技有限公司 | USB风扇、迷你风扇 | True / 0.572 | [True, True, True] | [True, True, True] |

## 字段覆盖率

| 字段 | 成功/已测试 | 三次一致/已测试 | 缺失原因（次数为商品数） |
| --- | --- | --- | --- |
| offer_id | 10/10 | 10/10 | {} |
| title | 10/10 | 10/10 | {} |
| price_raw | 8/10 | 10/10 | {'商品价格组件没有可见价格': 2} |
| min_order_qty | 5/10 | 10/10 | {'目标商品区域未找到唯一起批量': 5} |
| sales_raw | 10/10 | 10/10 | {} |
| visible_sku_names | 10/10 | 10/10 | {} |
| selected_sku_name | 6/10 | 10/10 | {'当前颜色/规格行无法唯一对应': 4} |
| selected_sku_price_raw | 6/10 | 10/10 | {'当前颜色/规格行无法唯一对应': 4} |
| selected_sku_availability | 5/10 | 10/10 | {'当前颜色/规格行无法唯一对应': 4, '该颜色没有可见可用数量输入及加号控件': 1} |
| selected_sku_stock_raw | 5/10 | 10/10 | {'当前颜色/规格行无法唯一对应': 5} |
| listed_at | 10/10 | 10/10 | {} |
| month_sales_raw | 10/10 | 10/10 | {} |
| month_distribution_raw | 10/10 | 10/10 | {} |
| year_sales_quantity_raw | 10/10 | 10/10 | {} |
| year_sales_orders_raw | 10/10 | 10/10 | {} |
| review_count_raw | 5/10 | 10/10 | {'助手栏未找到唯一可见标签值：评论数': 5} |
| positive_rate_raw | 5/10 | 10/10 | {'助手栏未找到唯一可见标签值：好评率': 5} |

## 商品 https://detail.1688.com/offer/1056305371784.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 1056305371784 | 1056305371784 | 1056305371784 |
| title | 抖音爆款usb充电加湿器家用大雾量空气净化器迷你无线加湿器批发 | 抖音爆款usb充电加湿器家用大雾量空气净化器迷你无线加湿器批发 | 抖音爆款usb充电加湿器家用大雾量空气净化器迷你无线加湿器批发 |
| price_raw | ¥79.00 | ¥79.00 | ¥79.00 |
| min_order_qty | unavailable | unavailable | unavailable |
| sales_raw | 已售80+台 | 已售80+台 | 已售80+台 |
| visible_sku_names | ['【白色】山水加湿器', '【绿色】山水加湿器', '【红色】山水加湿器', '【白黄色】山眠加湿器', '【黑黄色】山眠加湿器', '【白蓝色】山眠加湿器', '【黑蓝色】山眠加湿器'] | ['【白色】山水加湿器', '【绿色】山水加湿器', '【红色】山水加湿器', '【白黄色】山眠加湿器', '【黑黄色】山眠加湿器', '【白蓝色】山眠加湿器', '【黑蓝色】山眠加湿器'] | ['【白色】山水加湿器', '【绿色】山水加湿器', '【红色】山水加湿器', '【白黄色】山眠加湿器', '【黑黄色】山眠加湿器', '【白蓝色】山眠加湿器', '【黑蓝色】山眠加湿器'] |
| selected_sku_name | 标准版（标配 1 根棉棒） | 标准版（标配 1 根棉棒） | 标准版（标配 1 根棉棒） |
| selected_sku_price_raw | ¥79 | ¥79 | ¥79 |
| selected_sku_availability | available | available | available |
| selected_sku_stock_raw | 库存997台 | 库存997台 | 库存997台 |
| listed_at | 2026-06-10 | 2026-06-10 | 2026-06-10 |
| month_sales_raw | 10+ | 10+ | 10+ |
| month_distribution_raw | 10+ | 10+ | 10+ |
| year_sales_quantity_raw | 70+ | 70+ | 70+ |
| year_sales_orders_raw | 60+ | 60+ | 60+ |
| review_count_raw | 1 | 1 | 1 |
| positive_rate_raw | 100% | 100% | 100% |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 1, 'color_button_count': 7, 'visible_spec_row_count': 1, 'selected_color_count': 1}；三次结构一致：True。
缺失原因：{'min_order_qty': '目标商品区域未找到唯一起批量'}

## 商品 https://detail.1688.com/offer/1025228589646.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 1025228589646 | 1025228589646 | 1025228589646 |
| title | 未素usb充电加湿器家用大雾量空气净化器迷你无线加湿器批发 | 未素usb充电加湿器家用大雾量空气净化器迷你无线加湿器批发 | 未素usb充电加湿器家用大雾量空气净化器迷你无线加湿器批发 |
| price_raw | ¥89.00 / ¥95.00 | ¥89.00 / ¥95.00 | ¥89.00 / ¥95.00 |
| min_order_qty | 5件起批 | 5件起批 | 5件起批 |
| sales_raw | 已售900+件 | 已售900+件 | 已售900+件 |
| visible_sku_names | ['白色', '绿色', '酒红色', '白+棉棒5', '绿+棉棒5', '红+棉棒5'] | ['白色', '绿色', '酒红色', '白+棉棒5', '绿+棉棒5', '红+棉棒5'] | ['白色', '绿色', '酒红色', '白+棉棒5', '绿+棉棒5', '红+棉棒5'] |
| selected_sku_name | unavailable | unavailable | unavailable |
| selected_sku_price_raw | unavailable | unavailable | unavailable |
| selected_sku_availability | unavailable | unavailable | unavailable |
| selected_sku_stock_raw | unavailable | unavailable | unavailable |
| listed_at | 2026-02-26 | 2026-02-26 | 2026-02-26 |
| month_sales_raw | 90+ | 90+ | 90+ |
| month_distribution_raw | 40+ | 40+ | 40+ |
| year_sales_quantity_raw | 800+ | 800+ | 800+ |
| year_sales_orders_raw | 300+ | 300+ | 300+ |
| review_count_raw | unavailable | unavailable | unavailable |
| positive_rate_raw | unavailable | unavailable | unavailable |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 2, 'color_button_count': 0, 'visible_spec_row_count': 6, 'selected_color_count': 0}；三次结构一致：True。
缺失原因：{'review_count_raw': '助手栏未找到唯一可见标签值：评论数', 'positive_rate_raw': '助手栏未找到唯一可见标签值：好评率', 'selected_sku_name': '当前颜色/规格行无法唯一对应', 'selected_sku_price_raw': '当前颜色/规格行无法唯一对应', 'selected_sku_availability': '当前颜色/规格行无法唯一对应', 'selected_sku_stock_raw': '当前颜色/规格行无法唯一对应'}

## 商品 https://detail.1688.com/offer/976443859503.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 976443859503 | 976443859503 | 976443859503 |
| title | 2026跨境爆款分体式磁吸暖手宝usb充电二合一发热便捷性暖手宝宝 | 2026跨境爆款分体式磁吸暖手宝usb充电二合一发热便捷性暖手宝宝 | 2026跨境爆款分体式磁吸暖手宝usb充电二合一发热便捷性暖手宝宝 |
| price_raw | ¥45.00 / ¥50.00 | ¥45.00 / ¥50.00 | ¥45.00 / ¥50.00 |
| min_order_qty | 1台起批 | 1台起批 | 1台起批 |
| sales_raw | 已售1300+台 | 已售1300+台 | 已售1300+台 |
| visible_sku_names | ['404暖手宝白色', '404暖手宝黑色', '404暖手宝绿色', '404暖手宝粉色', '401暖手宝【请联系客服】', '白色404暖手宝+贴纸', '粉色404暖手宝+贴纸', '绿色404暖手宝+贴纸', '黑色404暖手宝+贴纸'] | ['404暖手宝白色', '404暖手宝黑色', '404暖手宝绿色', '404暖手宝粉色', '401暖手宝【请联系客服】', '白色404暖手宝+贴纸', '粉色404暖手宝+贴纸', '绿色404暖手宝+贴纸', '黑色404暖手宝+贴纸'] | ['404暖手宝白色', '404暖手宝黑色', '404暖手宝绿色', '404暖手宝粉色', '401暖手宝【请联系客服】', '白色404暖手宝+贴纸', '粉色404暖手宝+贴纸', '绿色404暖手宝+贴纸', '黑色404暖手宝+贴纸'] |
| selected_sku_name | 6000M&A领先版 | 6000M&A领先版 | 6000M&A领先版 |
| selected_sku_price_raw | ¥48 | ¥48 | ¥48 |
| selected_sku_availability | available | available | available |
| selected_sku_stock_raw | 库存1065台 | 库存1065台 | 库存1065台 |
| listed_at | 2025-09-16 | 2025-09-16 | 2025-09-16 |
| month_sales_raw | 20+ | 20+ | 20+ |
| month_distribution_raw | 10+ | 10+ | 10+ |
| year_sales_quantity_raw | 1300+ | 1300+ | 1300+ |
| year_sales_orders_raw | 1200+ | 1200+ | 1200+ |
| review_count_raw | 3 | 3 | 3 |
| positive_rate_raw | 100% | 100% | 100% |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 2, 'color_button_count': 9, 'visible_spec_row_count': 1, 'selected_color_count': 1}；三次结构一致：True。
缺失原因：{}

## 商品 https://detail.1688.com/offer/1045639948434.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 1045639948434 | 1045639948434 | 1045639948434 |
| title | 【小南瓜品牌方】网红电炖杯电煮锅家用学生宿舍用小煮锅【D8】 | 【小南瓜品牌方】网红电炖杯电煮锅家用学生宿舍用小煮锅【D8】 | 【小南瓜品牌方】网红电炖杯电煮锅家用学生宿舍用小煮锅【D8】 |
| price_raw | ¥49.90 / ¥69.90 | ¥49.90 / ¥69.90 | ¥49.90 / ¥69.90 |
| min_order_qty | 1台起批 | 1台起批 | 1台起批 |
| sales_raw | 已售10+台 | 已售10+台 | 已售10+台 |
| visible_sku_names | ['D8-B 机械款 喷涂款 黄色', 'D8-B 智能款 平盖 黄色', 'D8-B 智能 + 滤网款 平盖 黄色'] | ['D8-B 机械款 喷涂款 黄色', 'D8-B 智能款 平盖 黄色', 'D8-B 智能 + 滤网款 平盖 黄色'] | ['D8-B 机械款 喷涂款 黄色', 'D8-B 智能款 平盖 黄色', 'D8-B 智能 + 滤网款 平盖 黄色'] |
| selected_sku_name | unavailable | unavailable | unavailable |
| selected_sku_price_raw | unavailable | unavailable | unavailable |
| selected_sku_availability | unavailable | unavailable | unavailable |
| selected_sku_stock_raw | unavailable | unavailable | unavailable |
| listed_at | 2026-04-17 | 2026-04-17 | 2026-04-17 |
| month_sales_raw | <10 | <10 | <10 |
| month_distribution_raw | <10 | <10 | <10 |
| year_sales_quantity_raw | 10+ | 10+ | 10+ |
| year_sales_orders_raw | 10+ | 10+ | 10+ |
| review_count_raw | unavailable | unavailable | unavailable |
| positive_rate_raw | unavailable | unavailable | unavailable |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 2, 'color_button_count': 0, 'visible_spec_row_count': 3, 'selected_color_count': 0}；三次结构一致：True。
缺失原因：{'review_count_raw': '助手栏未找到唯一可见标签值：评论数', 'positive_rate_raw': '助手栏未找到唯一可见标签值：好评率', 'selected_sku_name': '当前颜色/规格行无法唯一对应', 'selected_sku_price_raw': '当前颜色/规格行无法唯一对应', 'selected_sku_availability': '当前颜色/规格行无法唯一对应', 'selected_sku_stock_raw': '当前颜色/规格行无法唯一对应'}

## 商品 https://detail.1688.com/offer/1068432029920.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 1068432029920 | 1068432029920 | 1068432029920 |
| title | 跨境创意篝火木屋香薰加湿器超声波雾化七彩灯光办公室车载香薰机 | 跨境创意篝火木屋香薰加湿器超声波雾化七彩灯光办公室车载香薰机 | 跨境创意篝火木屋香薰加湿器超声波雾化七彩灯光办公室车载香薰机 |
| price_raw | ¥50.00 | ¥50.00 | ¥50.00 |
| min_order_qty | unavailable | unavailable | unavailable |
| sales_raw | 已售20+个 | 已售20+个 | 已售20+个 |
| visible_sku_names | ['HY11【黑色】七色灯光+缺水断电+轻音运行', 'HY11【白色】七色灯光+缺水断电+轻音运行', 'HY11【浅木纹色】七色灯光+缺水断电+轻音运行', 'HY11【深木纹色】七色灯光+缺水断电+轻音运行'] | ['HY11【黑色】七色灯光+缺水断电+轻音运行', 'HY11【白色】七色灯光+缺水断电+轻音运行', 'HY11【浅木纹色】七色灯光+缺水断电+轻音运行', 'HY11【深木纹色】七色灯光+缺水断电+轻音运行'] | ['HY11【黑色】七色灯光+缺水断电+轻音运行', 'HY11【白色】七色灯光+缺水断电+轻音运行', 'HY11【浅木纹色】七色灯光+缺水断电+轻音运行', 'HY11【深木纹色】七色灯光+缺水断电+轻音运行'] |
| selected_sku_name | 英文彩盒+13国说明书 | 英文彩盒+13国说明书 | 英文彩盒+13国说明书 |
| selected_sku_price_raw | ¥50 | ¥50 | ¥50 |
| selected_sku_availability | available | available | available |
| selected_sku_stock_raw | 库存9999个 | 库存9999个 | 库存9999个 |
| listed_at | 2026-07-21 | 2026-07-21 | 2026-07-21 |
| month_sales_raw | <10 | <10 | <10 |
| month_distribution_raw | <10 | <10 | <10 |
| year_sales_quantity_raw | 20+ | 20+ | 20+ |
| year_sales_orders_raw | <10 | <10 | <10 |
| review_count_raw | 7 | 7 | 7 |
| positive_rate_raw | 100% | 100% | 100% |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 1, 'color_button_count': 4, 'visible_spec_row_count': 1, 'selected_color_count': 1}；三次结构一致：True。
缺失原因：{'min_order_qty': '目标商品区域未找到唯一起批量'}

## 商品 https://detail.1688.com/offer/1037232285050.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 1037232285050 | 1037232285050 | 1037232285050 |
| title | [APP款]桌面循环小风扇usb充电智能屏带氛围灯便携式办公桌面跨境 | [APP款]桌面循环小风扇usb充电智能屏带氛围灯便携式办公桌面跨境 | [APP款]桌面循环小风扇usb充电智能屏带氛围灯便携式办公桌面跨境 |
| price_raw | ¥65.00 / ¥75.00 | ¥65.00 / ¥75.00 | ¥65.00 / ¥75.00 |
| min_order_qty | 1台起批 | 1台起批 | 1台起批 |
| sales_raw | 已售30+台 | 已售30+台 | 已售30+台 |
| visible_sku_names | ['【灰夜紫】充电款', '【月光白】充电款', '【灰夜紫】APP充电款', '【月光白】APP充电款'] | ['【灰夜紫】充电款', '【月光白】充电款', '【灰夜紫】APP充电款', '【月光白】APP充电款'] | ['【灰夜紫】充电款', '【月光白】充电款', '【灰夜紫】APP充电款', '【月光白】APP充电款'] |
| selected_sku_name | / | / | / |
| selected_sku_price_raw | ¥65 | ¥65 | ¥65 |
| selected_sku_availability | unavailable | unavailable | unavailable |
| selected_sku_stock_raw | unavailable | unavailable | unavailable |
| listed_at | 2026-03-26 | 2026-03-26 | 2026-03-26 |
| month_sales_raw | <10 | <10 | <10 |
| month_distribution_raw | <10 | <10 | <10 |
| year_sales_quantity_raw | 30+ | 30+ | 30+ |
| year_sales_orders_raw | <10 | <10 | <10 |
| review_count_raw | unavailable | unavailable | unavailable |
| positive_rate_raw | unavailable | unavailable | unavailable |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 2, 'color_button_count': 4, 'visible_spec_row_count': 1, 'selected_color_count': 1}；三次结构一致：True。
缺失原因：{'review_count_raw': '助手栏未找到唯一可见标签值：评论数', 'positive_rate_raw': '助手栏未找到唯一可见标签值：好评率', 'selected_sku_availability': '该颜色没有可见可用数量输入及加号控件', 'selected_sku_stock_raw': '当前颜色/规格行无法唯一对应'}

## 商品 https://detail.1688.com/offer/989519678078.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 989519678078 | 989519678078 | 989519678078 |
| title | 多功能料理锅家用电炒锅一体式电火锅汤锅泡面锅煮粥煮饭多用DG9 | 多功能料理锅家用电炒锅一体式电火锅汤锅泡面锅煮粥煮饭多用DG9 | 多功能料理锅家用电炒锅一体式电火锅汤锅泡面锅煮粥煮饭多用DG9 |
| price_raw | ¥28.63 / ¥56.49 | ¥28.63 / ¥56.49 | ¥28.63 / ¥56.49 |
| min_order_qty | unavailable | unavailable | unavailable |
| sales_raw | 已售10+台 | 已售10+台 | 已售10+台 |
| visible_sku_names | ['2L奶油白智能预约【单锅】', '2L中国红智能预约【单锅】', '2L奶油白智能预约【PP蒸屉】', '2L中国红智能预约【PP蒸屉】', '2L奶油白智能预约【沥水篮+PP蒸屉】', '2L中国红智能预约【沥水篮+PP蒸屉】', '草绿色-单锅【容量1.8L】'] | ['2L奶油白智能预约【单锅】', '2L中国红智能预约【单锅】', '2L奶油白智能预约【PP蒸屉】', '2L中国红智能预约【PP蒸屉】', '2L奶油白智能预约【沥水篮+PP蒸屉】', '2L中国红智能预约【沥水篮+PP蒸屉】', '草绿色-单锅【容量1.8L】'] | ['2L奶油白智能预约【单锅】', '2L中国红智能预约【单锅】', '2L奶油白智能预约【PP蒸屉】', '2L中国红智能预约【PP蒸屉】', '2L奶油白智能预约【沥水篮+PP蒸屉】', '2L中国红智能预约【沥水篮+PP蒸屉】', '草绿色-单锅【容量1.8L】'] |
| selected_sku_name | unavailable | unavailable | unavailable |
| selected_sku_price_raw | unavailable | unavailable | unavailable |
| selected_sku_availability | unavailable | unavailable | unavailable |
| selected_sku_stock_raw | unavailable | unavailable | unavailable |
| listed_at | 2025-10-29 | 2025-10-29 | 2025-10-29 |
| month_sales_raw | <10 | <10 | <10 |
| month_distribution_raw | <10 | <10 | <10 |
| year_sales_quantity_raw | 10+ | 10+ | 10+ |
| year_sales_orders_raw | 10+ | 10+ | 10+ |
| review_count_raw | 2 | 2 | 2 |
| positive_rate_raw | 100% | 100% | 100% |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 2, 'color_button_count': 0, 'visible_spec_row_count': 7, 'selected_color_count': 0}；三次结构一致：True。
缺失原因：{'min_order_qty': '目标商品区域未找到唯一起批量', 'selected_sku_name': '当前颜色/规格行无法唯一对应', 'selected_sku_price_raw': '当前颜色/规格行无法唯一对应', 'selected_sku_availability': '当前颜色/规格行无法唯一对应', 'selected_sku_stock_raw': '当前颜色/规格行无法唯一对应'}

## 商品 https://detail.1688.com/offer/1062017117856.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 1062017117856 | 1062017117856 | 1062017117856 |
| title | 跨境JB爆款charge6冲钢印无线蓝牙音箱便携式户外低音炮小音响 | 跨境JB爆款charge6冲钢印无线蓝牙音箱便携式户外低音炮小音响 | 跨境JB爆款charge6冲钢印无线蓝牙音箱便携式户外低音炮小音响 |
| price_raw | unavailable | unavailable | unavailable |
| min_order_qty | unavailable | unavailable | unavailable |
| sales_raw | 已售30+件 | 已售30+件 | 已售30+件 |
| visible_sku_names | ['黑色钢印一机一码', '白色钢印一机一码', '黑橙钢印一机一码', '军绿色钢印一机一码', '蓝色钢印一机一码', '紫色钢印一机一码', '红色钢印一机一码', '粉红色钢印一机一码'] | ['黑色钢印一机一码', '白色钢印一机一码', '黑橙钢印一机一码', '军绿色钢印一机一码', '蓝色钢印一机一码', '紫色钢印一机一码', '红色钢印一机一码', '粉红色钢印一机一码'] | ['黑色钢印一机一码', '白色钢印一机一码', '黑橙钢印一机一码', '军绿色钢印一机一码', '蓝色钢印一机一码', '紫色钢印一机一码', '红色钢印一机一码', '粉红色钢印一机一码'] |
| selected_sku_name | unavailable | unavailable | unavailable |
| selected_sku_price_raw | unavailable | unavailable | unavailable |
| selected_sku_availability | unavailable | unavailable | unavailable |
| selected_sku_stock_raw | unavailable | unavailable | unavailable |
| listed_at | 2026-06-26 | 2026-06-26 | 2026-06-26 |
| month_sales_raw | <10 | <10 | <10 |
| month_distribution_raw | <10 | <10 | <10 |
| year_sales_quantity_raw | 30+ | 30+ | 30+ |
| year_sales_orders_raw | 10+ | 10+ | 10+ |
| review_count_raw | unavailable | unavailable | unavailable |
| positive_rate_raw | unavailable | unavailable | unavailable |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 0, 'color_button_count': 0, 'visible_spec_row_count': 8, 'selected_color_count': 0}；三次结构一致：True。
缺失原因：{'price_raw': '商品价格组件没有可见价格', 'min_order_qty': '目标商品区域未找到唯一起批量', 'review_count_raw': '助手栏未找到唯一可见标签值：评论数', 'positive_rate_raw': '助手栏未找到唯一可见标签值：好评率', 'selected_sku_name': '当前颜色/规格行无法唯一对应', 'selected_sku_price_raw': '当前颜色/规格行无法唯一对应', 'selected_sku_availability': '当前颜色/规格行无法唯一对应', 'selected_sku_stock_raw': '当前颜色/规格行无法唯一对应'}

## 商品 https://detail.1688.com/offer/933351766381.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 933351766381 | 933351766381 | 933351766381 |
| title | 手持新款涡轮手持户外便携风扇折叠迷你小风扇桌面挂钩 | 手持新款涡轮手持户外便携风扇折叠迷你小风扇桌面挂钩 | 手持新款涡轮手持户外便携风扇折叠迷你小风扇桌面挂钩 |
| price_raw | unavailable | unavailable | unavailable |
| min_order_qty | 2台起批 | 2台起批 | 2台起批 |
| sales_raw | 已售1000+台 | 已售1000+台 | 已售1000+台 |
| visible_sku_names | ['白色', '蓝色', '粉色'] | ['白色', '蓝色', '粉色'] | ['白色', '蓝色', '粉色'] |
| selected_sku_name | 198x85x32mm | 198x85x32mm | 198x85x32mm |
| selected_sku_price_raw | ¥5.5 | ¥5.5 | ¥5.5 |
| selected_sku_availability | available | available | available |
| selected_sku_stock_raw | 库存99669台 | 库存99669台 | 库存99669台 |
| listed_at | 2025-06-03 | 2025-06-03 | 2025-06-03 |
| month_sales_raw | <10 | <10 | <10 |
| month_distribution_raw | <10 | <10 | <10 |
| year_sales_quantity_raw | 1000+ | 1000+ | 1000+ |
| year_sales_orders_raw | <10 | <10 | <10 |
| review_count_raw | unavailable | unavailable | unavailable |
| positive_rate_raw | unavailable | unavailable | unavailable |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 0, 'color_button_count': 3, 'visible_spec_row_count': 1, 'selected_color_count': 1}；三次结构一致：True。
缺失原因：{'price_raw': '商品价格组件没有可见价格', 'review_count_raw': '助手栏未找到唯一可见标签值：评论数', 'positive_rate_raw': '助手栏未找到唯一可见标签值：好评率'}

## 商品 https://detail.1688.com/offer/1018928575894.html

读取错误：无

| 字段 | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| offer_id | 1018928575894 | 1018928575894 | 1018928575894 |
| title | 【已接入APP】2026新款夹子小风扇带数显桌面100档降温神器源头厂 | 【已接入APP】2026新款夹子小风扇带数显桌面100档降温神器源头厂 | 【已接入APP】2026新款夹子小风扇带数显桌面100档降温神器源头厂 |
| price_raw | ¥29.00 / ¥35.00 | ¥29.00 / ¥35.00 | ¥29.00 / ¥35.00 |
| min_order_qty | unavailable | unavailable | unavailable |
| sales_raw | 已售300+台 | 已售300+台 | 已售300+台 |
| visible_sku_names | ['灰紫色【充电款】', '米白色【充电款】', '浅绿色【充电款】', '灰紫色【充电APP款】', '米白色【APP充电款】', '浅绿色【APP充电款】'] | ['灰紫色【充电款】', '米白色【充电款】', '浅绿色【充电款】', '灰紫色【充电APP款】', '米白色【APP充电款】', '浅绿色【APP充电款】'] | ['灰紫色【充电款】', '米白色【充电款】', '浅绿色【充电款】', '灰紫色【充电APP款】', '米白色【APP充电款】', '浅绿色【APP充电款】'] |
| selected_sku_name | 141*82*175mm | 141*82*175mm | 141*82*175mm |
| selected_sku_price_raw | ¥29 | ¥29 | ¥29 |
| selected_sku_availability | available | available | available |
| selected_sku_stock_raw | 库存493台 | 库存493台 | 库存493台 |
| listed_at | 2026-02-05 | 2026-02-05 | 2026-02-05 |
| month_sales_raw | <10 | <10 | <10 |
| month_distribution_raw | <10 | <10 | <10 |
| year_sales_quantity_raw | 300+ | 300+ | 300+ |
| year_sales_orders_raw | 100+ | 100+ | 100+ |
| review_count_raw | 2 | 2 | 2 |
| positive_rate_raw | 50% | 50% | 50% |

商品区域识别：True；助手识别：True。
DOM结构：{'price_value_count': 2, 'color_button_count': 6, 'visible_spec_row_count': 1, 'selected_color_count': 1}；三次结构一致：True。
缺失原因：{'min_order_qty': '目标商品区域未找到唯一起批量'}

## 跨商品差异和 V1 判断

样本不足10个时，不对跨商品差异、跨店铺/品类覆盖率或正式V1可行性下结论。
当前采集器使用 .title-content h1 所在 .ms-container 商品区域，读取唯一价格组件；支持可见颜色按钮或已展示规格行名称。多价格分别保留文本并用换行分隔，不推算区间。无默认选中、多规格行时，当前SKU字段返回unavailable，不把第一行当作默认。
available仅代表当前数量输入和加号控件可用，不能保证真实下单或库存。三次读取间隔2秒，不证明刷新或重启稳定。
V1候选的最终取舍须依据覆盖率和缺失来源判断；当前规格、价格、库存、控件可用状态不能要求每个商品都有值。
本阶段不采集完整SKU组合，现货率不以揽收率代替；本轮结束后不自动开发V1。

## 最终证据与缺失分类

CDP恢复成功。10个用户提供商品均正式读取3次、商品区识别10/10、助手识别10/10；17个字段的逐字段三次一致数均10/10，包括一致的unavailable。10次等待均在上限内达到就绪，未发生等待超时。原9商品证据保留于debug/first_nine_reads.json，最终证据为debug/coverage_reads.json；诊断DOM为debug/dom_diagnostics.json。

稳定等待只判断关键DOM结构开始就绪，不保证每个字段存在，不将多价格缺失视为未准备好；缺失字段仍保留unavailable。

### A：页面加载时序导致的缺失

上一轮1045639948434、1068432029920首读商品区不可识别、随后可读。增加等待后，本轮两商品标题、价格、销量及可见SKU名称均3次可读且一致；等待未补造字段值。香薰机起批量本轮仍缺失，属于下面C。通过历史读取变化及本次复验支持时序判断，不声称已经验证网络级根因。

| 核心字段 | 旧9商品成功数 | 新同9商品成功数 | 最终10商品成功数 |
| --- | --- | --- | --- |
| title | 7/9 | 9/9 | 10/10 |
| price_raw | 5/9 | 7/9 | 8/10 |
| min_order_qty | 5/9 | 5/9 | 5/10 |
| sales_raw | 7/9 | 9/9 | 10/10 |
| visible_sku_names | 7/9 | 9/9 | 10/10 |

### B：商品/助手没有展示可确认的目标值

评论数、好评率：1025228589646、1045639948434、1037232285050、1062017117856、933351766381，助手实际展示“-”，来源占位值，无精确数值可取；5商品失败，不当作0。

当前选中SKU字段：1025228589646、1045639948434、989519678078、1062017117856直接展示多个规格行，没有唯一默认或已选SKU，4商品无法确定当前SKU。虽然多行价格和库存可见，也不采用第一行或自动点击选择。

1037232285050已选规格原文为“/”，保留该展示值但不解释其业务含义；未找到可确认的库存展示值和可用数量输入/加号组合，当前库存及可售状态仍unavailable，不凭价格存在推断可售。缺少可确认状态不能证明不可售。

### C：当前定位规则不支持（DOM实际已有值）

price_raw：1062017117856、933351766381使用3个阶梯价格组件，当前规则要求唯一价格组件，故2商品失败。DOM实际分别展示“¥125.00 / ¥117.00 / ¥110.00”及“¥5.50 / ¥5.00 / ¥4.80”，这里仅作为诊断证据，不回填正式采集结果，也不选择最低价作为当前价格。

min_order_qty：1056305371784、1068432029920、989519678078、1062017117856、1018928575894，起批量在带“60天老客价”子节点的p内，现规则只匹配叶节点，故5商品失败。实际分别有“1台起批”“1个起批”“1台起批”“1件起批”“1台起批”。这是通用定位限制，不是商品未展示。等待无法解决该限制；本轮按要求只修等待，不堆兼容实现。

## 商品与助手覆盖率分别判断

商品区：offer_id、title、sales_raw、visible_sku_names均10/10；price_raw 8/10；min_order_qty 5/10；当前规格及价格6/10，当前可售控件状态及库存5/10。

助手：上架时间、月成交、月代销、年成交件数、年成交笔数均10/10；评论数、好评率各5/10。来源占位值造成50%覆盖，不建议通过猜测或接口绕过填补。

## 跨商品DOM差异和样本限制

9个可识别店铺；助手类目为加湿器2、电暖手宝1、电煮锅2、香薰机1、USB风扇/迷你风扇3、蓝牙音箱1。按用户实际指定样本执行，没有为凑“每类2个”搜索商品。所有10商品均识别助手，但不能证明站点所有布局或插件未来版本可读。

商品主价格有单价、双端点展示、3档阶梯价；SKU有颜色按钮加单行规格、直接多行规格且无默认选中；起批段落有纯文本和夹有老客价标签两类。三次DOM结构均一致；等待消除了本轮早期空商品区，不等于跨重启、刷新、不同网络时延长期稳定。

原始“<10”“10+”“已售80+台”“50%”等字符串全部保留。双端点价格以换行保留两段展示文本，表格以斜杠展示换行，不推算精准价格或数量。数据跨轮变化（例如原商品年成交70+、库存997台）采用当轮页面实值，不能把跨轮业务变化误算成三次读取不一致。

## V1字段取舍与是否结束POC

| 建议 | 字段 | 理由/边界 |
| --- | --- | --- |
| 核心 | offer_id、title、sales_raw、visible_sku_names；listed_at、month_sales_raw、month_distribution_raw、year_sales_quantity_raw、year_sales_orders_raw | 本样本10/10可读且一致；助手原始展示统计，不承诺精确数字 |
| 业务核心候选，当前不能设为必成功 | price_raw | 8/10；正式V1前须定义阶梯价原始展示的表达方式，或允许该字段unavailable，不可默认最低价 |
| 可选 | min_order_qty | 5/10；真实字段存在但叶节点规则不足，后续若有业务必要只做通用文本段定位 |
| 可选 | selected_sku_name、selected_sku_price_raw、selected_sku_availability、selected_sku_stock_raw | 6/10或5/10；无唯一已选SKU时合法缺失；available只是数量控件可用状态 |
| 可选 | review_count_raw、positive_rate_raw | 各5/10；来源占位值不能恢复成精确值 |
| 删除/排除必须项 | 完整SKU遍历、所有SKU独立价格、精确化模糊销量、保证真实可售、现货率的错误替代 | 本阶段未验证或语义不成立；不删除已请求字段的原始输出槽位 |

**建议结束本轮数据采集可行性POC。可以进入范围明确、允许缺失的个人V1立项讨论，但不建议直接按“全字段必成功、可靠价格监控”的正式V1开发。** 标题、可见名称、销量及助手前5指标已得到可行性证据；若正式V1必须完整价格，则先定义阶梯价语义并对两种通用缺口做小范围验证，仍不堆商品特例。本轮不实现上述后续修正，不开发V1。

## 验证与复现

稳定等待回归检查覆盖：空DOM连续相同不就绪、就绪节点变化后重新连续匹配、10秒超时。既有原始文本和无默认SKU检查、URL输入边界、Python编译、10商品30次结果断言和git diff --check通过。仅改POC目录；正式data/order_calendar.json原有用户改动未触碰。

```powershell
$sampleArgs=@("poc/1688_monitor/coverage.py")
Get-Content poc/1688_monitor/sample_urls.txt | ForEach-Object {$sampleArgs+=@("--url",$_)}
& poc/1688_monitor/.venv/Scripts/python.exe @sampleArgs
```

复现只连接已有Chrome，不启动Chrome；只访问用户已指定URL，复用已有标签，不切换SKU，不调用接口、破解助手或处理验证码。

## 最终采集层收口（本章为最终结论，前文章节保留修正历史）

**采集层POC正式结束：通过用户规定的收口标准。** 只修多价格/阶梯价格读取及起批量文本定位，没有商品ID特例、正式业务改动、数据库、UI或V1开发。

### 两处通用修正

价格：在已确认 `.title-content h1` 所在主采购 `.ms-container` 局部区域中，读取所有可见 `.price-component` 的可见 `.price-info`，按页面DOM展示顺序输出 `price_raw_values: []`。保留人民币符号和小数原文，仅拼合页面分段展示的可见价格文字，不取最低/最高价，不排序，不数值化、不推算区间、不把SKU价格混入主价格列表。空列表表示没有确认的价格，同时记录unavailable原因；空列表不计成功。旧商品标量price_raw已由新列表取代，已选SKU的原始独立价格保持不变。

阶梯：只有同一价格组件内唯一可见价格，及唯一数量段落的明确直接文本能对应时，输出 `price_tiers`。单价起批也可明确对应；双价格端点与同一数量段落无法一一对应时返回空阶梯列表，不影响price_raw_values获取。10商品有4个可明确对应，6个为空；三次对应结果一致。

起批：只从上述采购价格局部区域的可见文本匹配“数字 + 件/台/个等明确单位 + 起批”，不要求叶节点，保留匹配原文。老客价子元素不会阻止匹配；重复相同值去重，多种不同起批值仍拒绝猜测。

### 修正前后覆盖率与核心回归

成功指每商品三次均明确取得非缺失值，价格列表须非空；一致指三次值相同，缺失值一致不等于成功。

| 字段 | 修正前 | 修正后 | 三次一致 |
| --- | --- | --- | --- |
| offer_id | 10/10 | 10/10 | 10/10 |
| title | 10/10 | 10/10 | 10/10 |
| price_raw_values | 8/10（旧price_raw） | 10/10 | 10/10 |
| min_order_qty | 5/10 | 10/10 | 10/10 |
| sales_raw | 10/10 | 10/10 | 10/10 |
| visible_sku_names | 10/10 | 10/10 | 10/10 |
| selected_sku_name | 6/10 | 6/10 | 10/10 |
| selected_sku_price_raw | 6/10 | 6/10 | 10/10 |
| selected_sku_availability | 5/10 | 5/10 | 10/10 |
| selected_sku_stock_raw | 5/10 | 5/10 | 10/10 |
| listed_at | 10/10 | 10/10 | 10/10 |
| month_sales_raw | 10/10 | 10/10 | 10/10 |
| month_distribution_raw | 10/10 | 10/10 | 10/10 |
| year_sales_quantity_raw | 10/10 | 10/10 | 10/10 |
| year_sales_orders_raw | 10/10 | 10/10 | 10/10 |
| review_count_raw | 5/10 | 5/10 | 10/10 |
| positive_rate_raw | 5/10 | 5/10 | 10/10 |

### 10商品最终价格与起批量

| offer_id | price_raw_values（原顺序） | min_order_qty | 明确可对应的price_tiers |
| --- | --- | --- | --- |
| 1056305371784 | ["¥79.00"] | 1台起批 | [{"qty_raw": "1台起批", "price_raw": "¥79.00"}] |
| 1025228589646 | ["¥89.00", "¥95.00"] | 5件起批 | [] |
| 976443859503 | ["¥45.00", "¥50.00"] | 1台起批 | [] |
| 1045639948434 | ["¥49.90", "¥69.90"] | 1台起批 | [] |
| 1068432029920 | ["¥50.00"] | 1个起批 | [{"qty_raw": "1个起批", "price_raw": "¥50.00"}] |
| 1037232285050 | ["¥65.00", "¥75.00"] | 1台起批 | [] |
| 989519678078 | ["¥28.63", "¥56.49"] | 1台起批 | [] |
| 1062017117856 | ["¥125.00", "¥117.00", "¥110.00"] | 1件起批 | [{"qty_raw": "1件起批", "price_raw": "¥125.00"}, {"qty_raw": "100-999件", "price_raw": "¥117.00"}, {"qty_raw": "≥1000件", "price_raw": "¥110.00"}] |
| 933351766381 | ["¥5.50", "¥5.00", "¥4.80"] | 2台起批 | [{"qty_raw": "2台起批", "price_raw": "¥5.50"}, {"qty_raw": "1000-9999台", "price_raw": "¥5.00"}, {"qty_raw": "≥10000台", "price_raw": "¥4.80"}] |
| 1018928575894 | ["¥29.00", "¥35.00"] | 1台起批 | [] |

### 最终V1字段取舍

| 类别 | 字段/能力 | 边界 |
| --- | --- | --- |
| 核心 | offer_id、title、price_raw_values、min_order_qty、sales_raw、visible_sku_names | 本次均10/10、三次一致；价格是展示列表，不是单一成交价，SKU仅表示当前可见名称 |
| 核心 | listed_at、month_sales_raw、month_distribution_raw、year_sales_quantity_raw、year_sales_orders_raw | 本次均10/10；保留助手原始字符串，不承诺精确销量 |
| 可选 | price_tiers | 4/10可明确对应；不建立不可靠数量映射 |
| 可选 | selected_sku_name、selected_sku_price_raw | 各6/10；仅当前唯一已选规格，不遍历全部组合 |
| 可选 | selected_sku_availability、selected_sku_stock_raw | 各5/10；available仅是可见数量控件可用，不保证真实可售或实际库存 |
| 可选 | review_count_raw、positive_rate_raw | 各5/10；助手“-”是合法来源缺失，不填0 |

### 明确不再继续研究的字段或能力

完整SKU组合和所有SKU独立价格遍历；无数量上下文的所谓单一“主价格”；模糊销量的精确化；隐藏DOM价格回填；未展示的现货率及以揽收率代替现货率；真实可售保证；趋势面板完整解析。本轮不增加剩余页面特例、不逆向接口或助手、不处理验证码。

剩余可选字段缺失仍来自无默认选中SKU、未展示可确认库存/数量控件状态及助手占位值，没有为填满覆盖率继续兼容。原先A类首读时序问题由已有稳定等待处理，原先C类价格和起批定位缺口已被本次通用修正消除；不将来源未展示当成技术成功。

### 验证证据与最终结束判断

仍连接用户现有 `http://127.0.0.1:9222`，复用10个原商品标签页与登录、官方助手，未启动Chrome或切换SKU。每商品先用已有最多10秒稳定等待，再正式读取3次、间隔2秒，共30次；全部字段三次一致，全部商品区及助手均识别。原核心字段覆盖率保持10/10，无明显回归。

修正前证据 `debug/before_closeout_reads.json`；修正后证据 `debug/coverage_reads.json`。本报告前文保留旧模型及旧读取结果，最终值以本章和修正后JSON为准。

DOM回归检查验证：阶梯价原顺序、隐藏及采购区外节点排除、双端点不猜阶梯对应、带老客价子元素的起批量、无价格时空列表。原始文本、未选SKU不当默认、空价格列表不计成功、稳定等待、URL边界、编译、30次实测断言及git diff --check通过。所有代码改动局限POC目录，原有正式业务用户改动未触碰。

**price_raw_values 10/10 ≥ 9/10；min_order_qty 10/10 ≥ 8/10；核心字段无回归：采集层POC正式结束。** 证据支持按以上核心/可选范围进入个人V1的后续需求与开发决策，但10样本短时间一致性不保证长期站点DOM稳定、价格可比性或销量精确性。本轮立即停止，不开始正式V1。
