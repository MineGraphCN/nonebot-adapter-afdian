更新 （2025年5月14日）
根据订单号查询随机自动回复

接口：https://ifdian.net/api/open/query-random-reply 

参数：out_trade_no，指定订单号查询信息，如需要查多个，则英文逗号分隔

返回数据：

{
    "ec": 200,
    "em": "success",
    "data": {
        "list": [{
            "out_trade_no": "202505141538455397541020050",
            "content": "999"
        }]
    }
}


通过API 填入随机自动回复 （补货、发码等功能）

接口： /api/open/update-plan-reply

参数：

plan_id 方案id

sku_id 型号id

二选一，如果是更新订阅方案，传plan_id，如果是更新商品，需要传sku_id

两个参数只能选一个，商品传plan_id会报错

auto_reply 自动回复内容，非必填，这个字段如果不为空，会覆盖原自动回复内容，不传或者传空字符串，不会更新自动回复内容

auto_random_reply 自动随机回复内容，非必填，如果不为空，才会去更新自动随机回复内容

update_random_reply_type 更新自动随机回复内容的方式，如果需要更新自动随机回复，这个字段是必填项，否则不会更新自动随机回复

  有两种取值：

  1、append追加，追加的方式，爱发电会在内容前面增加一个换行符

  2、overwrite覆盖，直接覆盖原内容

更新（2025年7月01日）
webhook增加签名



更新（2025年8月14日）
user_id: 上面的 user_id，表明你是谁 params: 具体接口传参的json字符串 ts: 发出请求时秒级时间戳 sign: 针对上面3个数据的签名，防止伪造数据。 sign 的计算规则为：md5(token+请求数据按key排序拼接key和value)

发送私信
/api/open/send-msg
params：
recipient-接收用户
content-私信内容

频率限制，10/s和1000/h

查看方案
/api/open/query-plan
params：
plan_id-方案id

返回参数
{
        "ec": 200,
        "em": "\u83b7\u53d6\u65b9\u6848\u6210\u529f",
        "data": {
                "plan": {
                        "plan_id": "436af0d0e0xxxxxxxxxxxxxx25c377",
                        "price": "5.00",
                        "name": "\u6d4b\u8bd5\u552e\u5356\u52a8\u60012",
                        "product_type": 1, //0-订阅 1-商品 2-捆绑包 3-自选包 4-售票
                        "desc": "",
                        "reply_content": "",
                        "replay_random_content": "",
             "independent": 0, //是否独立方案0-非独立 1-独立
                     "permanent": 0, //是否永久方案 0-非永久 1-永久
                     "pay_month": 1, //1-月费，3-季费，12-年费
                        "skus": [{
                                "sku_id": "436eba6cexxxxxxxxxxxxxx025c377",
                                "plan_id": "436af0d0e0xxxxxxxxxxxxxx25c377",
                                "name": "\u578b\u53f71",
                                "desc": "",
                                "stock": "",
                                "price": "5.00",
                                "reply_content": "",
                                "reply_random_content": ""
                        }]
                }
        }
}
方案类型是订阅时，不会有skus字段