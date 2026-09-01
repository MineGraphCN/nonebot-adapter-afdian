import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from nonebug import App
import pytest

from nonebot.adapters.afdian.payload import Order
from nonebot.adapters.afdian.signature import verify_webhook_sign


@pytest.fixture(scope="module")
def key_pair():
    """生成测试用 RSA 密钥对"""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = (
        private_key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_key, public_pem


@pytest.fixture
def order() -> Order:
    return Order(
        out_trade_no="2025080112345678901234567890",
        user_id="adf397fe8374811eaacee52540025c377",
        plan_id="a45353328af911eb973052540025c377",
        month=1,
        total_amount="5.00",
        show_amount="5.00",
        status=2,
        product_type=0,
    )


def sign_order(private_key, order: Order) -> str:
    sign_str = (
        f"{order.out_trade_no}{order.user_id}{order.plan_id}{order.total_amount}"
    ).encode()
    signature = private_key.sign(sign_str, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode()


def test_verify_sign_valid(key_pair, order):
    private_key, public_pem = key_pair
    order.sign = sign_order(private_key, order)
    assert verify_webhook_sign(order, public_pem)


def test_verify_sign_invalid(key_pair, order):
    private_key, public_pem = key_pair
    # 用篡改的金额生成签名，验证应失败
    sign_str = f"{order.out_trade_no}{order.user_id}{order.plan_id}9.99".encode()
    signature = private_key.sign(sign_str, padding.PKCS1v15(), hashes.SHA256())
    order.sign = base64.b64encode(signature).decode()
    assert not verify_webhook_sign(order, public_pem)


def test_verify_sign_wrong_key(key_pair, order):
    private_key, _ = key_pair
    other_public_pem = (
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        .public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    order.sign = sign_order(private_key, order)
    assert not verify_webhook_sign(order, other_public_pem)


def test_verify_sign_empty(order):
    assert not verify_webhook_sign(order)


@pytest.mark.asyncio
async def test_webhook_sign_valid(app: App, key_pair, monkeypatch):
    private_key, public_pem = key_pair
    # 替换适配器使用的默认公钥
    monkeypatch.setattr(
        "nonebot.adapters.afdian.adapter.AFDIAN_WEBHOOK_PUBLIC_KEY", public_pem
    )

    file_path = Path(__file__).parent / "events.json"
    with open(file_path, encoding="utf-8") as f:  # noqa: ASYNC230
        test_data = json.load(f)
    # 换成非测试订单号，并附带签名
    order_data = test_data["data"]["order"]
    order_data["out_trade_no"] = "2025080112345678901234567890"
    order_data["sign"] = sign_order(private_key, Order.model_validate(order_data))

    async with app.test_server() as ctx:
        client = ctx.get_client()
        response = await client.post("/afdian/webhooks/fake", json=test_data)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_sign_invalid(app: App, key_pair, monkeypatch):
    private_key, public_pem = key_pair
    monkeypatch.setattr(
        "nonebot.adapters.afdian.adapter.AFDIAN_WEBHOOK_PUBLIC_KEY", public_pem
    )

    file_path = Path(__file__).parent / "events.json"
    with open(file_path, encoding="utf-8") as f:  # noqa: ASYNC230
        test_data = json.load(f)
    order_data = test_data["data"]["order"]
    order_data["out_trade_no"] = "2025080112345678901234567890"
    # 用篡改的金额签名
    sign_str = (
        f"{order_data['out_trade_no']}{order_data['user_id']}"
        f"{order_data['plan_id']}9.99"
    ).encode()
    signature = private_key.sign(sign_str, padding.PKCS1v15(), hashes.SHA256())
    order_data["sign"] = base64.b64encode(signature).decode()

    async with app.test_server() as ctx:
        client = ctx.get_client()
        response = await client.post("/afdian/webhooks/fake", json=test_data)
        assert response.status_code == 400
        assert response.json()["em"] == "sign verify failed"
