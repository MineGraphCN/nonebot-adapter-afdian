import json
from urllib.parse import parse_qs, urlsplit

from nonebug import App
import pytest

from nonebot import get_adapter
from nonebot.adapters.afdian import Adapter, TokenBot
from nonebot.adapters.afdian.exception import ApiNotAvailable
from nonebot.adapters.afdian.payload import PlanResponse


@pytest.mark.asyncio
async def test_new_api_methods(app: App, monkeypatch):
    adapter = get_adapter(Adapter)
    bot = TokenBot(adapter, self_id="fake", token="test-token")

    calls: list[dict] = []

    def last_params() -> dict:
        query = parse_qs(urlsplit(next(iter(calls[-1].values()))).query)
        return query["params"][0]

    async def fake_request(request):
        from nonebot.drivers import Response

        url = str(request.url)
        calls.append({url: url})
        if "query-random-reply" in url:
            content = '{"ec":200,"em":"success","data":{"list":[{"out_trade_no":"123","content":"999"}]}}'
        elif "update-plan-reply" in url:
            content = '{"ec":200,"em":"success","data":{}}'
        elif "send-msg" in url:
            content = '{"ec":200,"em":"success","data":{}}'
        elif "query-plan" in url:
            content = (
                '{"ec":200,"em":"获取方案成功","data":{"plan":{"plan_id":"p1",'
                '"price":"5.00","name":"测试","product_type":1,"skues":null,'
                '"skus":[{"sku_id":"s1","plan_id":"p1","name":"型号1","price":"5.00"}]}}}'
            )
        else:
            content = '{"ec":200,"em":"ok","data":{}}'
        return Response(200, content=content)

    monkeypatch.setattr(adapter, "request", fake_request)

    # query_random_reply
    resp = await bot.query_random_reply("202505141538455397541020050")
    assert resp.data.list[0].content == "999"
    resp = await bot.query_random_reply(["111", "222"])
    assert "111,222" in last_params()

    # update_plan_reply 参数校验
    with pytest.raises(ValueError, match="mutually exclusive"):
        await bot.update_plan_reply()
    with pytest.raises(ValueError, match="mutually exclusive"):
        await bot.update_plan_reply(plan_id="p1", sku_id="s1")
    with pytest.raises(ValueError, match="update_random_reply_type is required"):
        await bot.update_plan_reply(plan_id="p1", auto_random_reply="code1")

    resp = await bot.update_plan_reply(
        plan_id="p1", auto_random_reply="code1", update_random_reply_type="append"
    )
    assert resp.ec == 200
    assert json.loads(last_params())["update_random_reply_type"] == "append"

    resp = await bot.update_plan_reply(sku_id="s1", auto_reply="reply")
    assert json.loads(last_params())["sku_id"] == "s1"

    # send_msg
    resp = await bot.send_msg("user1", "hello")
    assert resp.ec == 200
    assert json.loads(last_params())["recipient"] == "user1"

    # query_plan
    resp = await bot.query_plan("p1")
    assert isinstance(resp, PlanResponse)
    assert resp.data.plan.product_type == 1
    assert resp.data.plan.skus[0].sku_id == "s1"


@pytest.mark.asyncio
async def test_call_api_dispatch(app: App, monkeypatch):
    """通过通用 bot.call_api 调用 API 应实际发出请求并解析响应"""
    adapter = get_adapter(Adapter)
    bot = TokenBot(adapter, self_id="fake", token="test-token")

    async def fake_request(request):
        from nonebot.drivers import Response

        return Response(
            200,
            content='{"ec":200,"em":"pong","data":{"list":[{"out_trade_no":"123","content":"999"}]}}',
        )

    monkeypatch.setattr(adapter, "request", fake_request)

    resp = await bot.call_api("/api/open/query-random-reply", out_trade_no="123")
    assert resp.ec == 200
    assert resp.data.list[0].content == "999"

    # 不支持的端点
    with pytest.raises(ApiNotAvailable):
        await bot.call_api("/api/open/unknown")
