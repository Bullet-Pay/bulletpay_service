
import web3

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_keys import keys


from brownie import accounts as a
from brownie import Erc20, BulletPay

def test_deploy_contracts():
    # Deploy Erc20
    mock_token = Erc20.deploy(1000000 * 10**6, "Mock USDC", 6, "mUSDC", {'from': a[0], 'gas_price': 1950000000})

    # Deploy BulletPay
    bulletpay = BulletPay.deploy(mock_token.address, {'from': a[0], 'gas_price': 1950000000})

    # Assert Erc20 deployment
    assert mock_token.name() == "Mock USDC"
    assert mock_token.symbol() == "mUSDC"
    assert mock_token.decimals() == 6
    assert mock_token.totalSupply() == 1000000 * 10**6

    # Assert BulletPay deployment
    assert bulletpay.token() == mock_token.address
    assert bulletpay.next_topup_id() == 1

def test_topup():
    # Deploy Erc20
    mock_token = Erc20.deploy(1000000 * 10**6, "Mock USDC", 6, "mUSDC", {'from': a[0], 'gas_price': 1950000000})

    # Deploy BulletPay
    bulletpay = BulletPay.deploy(mock_token.address, {'from': a[0], 'gas_price': 1950000000})

    bulletpay.topup(100* 10**6, a[1], {'from': a[0], 'gas_price': 1950000000})

