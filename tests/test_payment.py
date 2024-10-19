
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

    mock_token.approve(bulletpay.address, 100* 10**6, {'from': a[0], 'gas_price': 1950000000})
    bulletpay.topup(100* 10**6, a[1], {'from': a[0], 'gas_price': 1950000000})
    assert mock_token.balanceOf(bulletpay) == 100* 10**6
    assert bulletpay.total() == 100* 10**6

def test_pay_to():
    # Deploy Erc20
    mock_token = Erc20.deploy(1000000 * 10**6, "Mock USDC", 6, "mUSDC", {'from': a[0], 'gas_price': 1950000000})

    # Deploy BulletPay
    bulletpay = BulletPay.deploy(mock_token.address, {'from': a[0], 'gas_price': 1950000000})

    PAYMENT_AMOUNT = 5 * 10**6  # 5 USDC
    PRIVATE_KEY = "0x1234567890123456789012345678901234567890123456789012345678901234"
    private_key_bytes = bytes.fromhex(PRIVATE_KEY[2:])
    private_key = keys.PrivateKey(private_key_bytes)
    SPENDER_ADDEESS = private_key.public_key.to_checksum_address()
    TO_ADDRESS = a[1].address

    mock_token.approve(bulletpay.address, 100* 10**6, {'from': a[0], 'gas_price': 1950000000})
    bulletpay.topup(100* 10**6, SPENDER_ADDEESS, {'from': a[0], 'gas_price': 1950000000})
    assert mock_token.balanceOf(bulletpay) == 100* 10**6
    assert bulletpay.total() == 100* 10**6

    hash1 = web3.Web3.solidity_keccak(['address', 'uint256'], [TO_ADDRESS, PAYMENT_AMOUNT])
    # print(hash1.hex())
    # hash2 = web3.Web3.solidity_keccak(['bytes', 'bytes32'], [b"\x19Ethereum Signed Message:\n32", hash1])
    # print(hash2.hex())

    # Sign the message using personal_sign
    # signature = Account.signHash(hash2, private_key=PRIVATE_KEY)
    # v, r, s = signature.v, signature.r, signature.s
    # signature_bytes =  r.to_bytes(32, 'big') + s.to_bytes(32, 'big') + bytes([v])
    message = encode_defunct(hexstr=hash1.hex())
    signed_message = Account.sign_message(message, private_key=PRIVATE_KEY)
    signature_bytes = signed_message.signature

    # Call pay_to
    tx = bulletpay.pay_to(1, TO_ADDRESS, PAYMENT_AMOUNT, signature_bytes, {'from': a[0], 'gas_price': 1950000000})

    # Assert the payment event
    # assert tx.events['AccountClosed']['accountId'] == 1
    # assert tx.events['AccountClosed']['creator'] == a[0]
    # assert tx.events['AccountClosed']['remainingBalance'] == DEPOSIT_AMOUNT - PAYMENT_AMOUNT

    # assert mock_token.balanceOf(TO_ADDRESS) == PAYMENT_AMOUNT
    # assert mock_token.balanceOf(a[0]) == 1000000 * 10**18 - DEPOSIT_AMOUNT + (DEPOSIT_AMOUNT - PAYMENT_AMOUNT)
    # assert mock_token.balanceOf(sub_account_payment.address) == 0

    # account = sub_account_payment.accounts(1)
    # assert account[2] == True
