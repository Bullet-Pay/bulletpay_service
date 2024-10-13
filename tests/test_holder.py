

from brownie import accounts as a
from brownie import ShareHolder, Erc20


def _test_submit_contribution_and_redistribute():
    operator = a[0]
    mock_token = Erc20.deploy(1000000 * 10**18, "Mock Token", 18, "MTK", {'from': a[0], 'gas_price': 1950000000})
    # Deploy the ShareHolder contract
    holder = ShareHolder.deploy(mock_token, {"from": operator, 'gas_price': 1950000000})
    assert holder.get_shares(operator) == 10**20

    # Add a contribution
    holder.submit_contribution(a[1], 10**17 * 3, {"from": operator, 'gas_price': 1950000000})
    holder.submit_contribution(a[2], 10**17 * 7, {"from": operator, 'gas_price': 1950000000})
    holder.redistribute({"from": operator, 'gas_price': 1950000000})

    balance = holder.get_shares(operator)
    assert balance == 10**20  * 99 // 100
    assert holder.get_shares(a[1]) == 10**17 * 3
    assert holder.get_shares(a[2]) == 10**17 * 7

# Test update_finance_quota
def test_update_finance_quota():
    operator = a[0]
    mock_token = Erc20.deploy(1000000 * 10**18, "Mock Token", 18, "MTK", {'from': a[0], 'gas_price': 1950000000})
    holder = ShareHolder.deploy(mock_token, {"from": operator, 'gas_price': 1950000000})

    holder.update_finance_quota(100, 1000, {"from": operator, 'gas_price': 1950000000})
    quota = holder.available_finance_quota(0)
    assert quota[0] == 100  # price
    assert quota[1] == 1000  # amount

    holder.update_finance_quota(100, 500, {"from": operator, 'gas_price': 1950000000})
    updated_quota = holder.available_finance_quota(0)
    assert updated_quota[0] == 100  # price
    assert updated_quota[1] == 1500  # amount (1000 + 500)

    holder.update_finance_quota(200, 2000, {"from": operator, 'gas_price': 1950000000})
    new_quota = holder.available_finance_quota(1)
    assert new_quota[0] == 200  # price
    assert new_quota[1] == 2000  # amount

    holder.update_finance_quota(100, -300, {"from": operator, 'gas_price': 1950000000})
    final_quota = holder.available_finance_quota(0)
    assert final_quota[0] == 100  # price
    assert final_quota[1] == 1200  # amount (1500 - 300)

    # Try to update quota as non-operator (should fail)
    # try:
    #     holder.update_finance_quota(100, 100, {"from": a[1], 'gas_price': 1950000000})
    #     assert False, "Non-operator was able to update finance quota"
    # except Exception as e:
    #     assert "operator required" in str(e)

    # Mint mock tokens
    mint_amount = 10000 * 10**18
    mock_token.transfer(a[1], mint_amount, {"from": a[0], 'gas_price': 1950000000})
    mock_token.approve(holder.address, mint_amount, {"from": a[1], 'gas_price': 1950000000})

    purchase_amount = 1000
    holder.purchase_finance_shares(100, purchase_amount, {"from": a[1], 'gas_price': 1950000000})
    assert holder.finance_shares(a[1]) == purchase_amount
    assert holder.total_finance_shares() == purchase_amount

    # Check if the quota was updated correctly after purchase
    updated_quota_after_purchase = holder.available_finance_quota(0)
    assert updated_quota_after_purchase[0] == 100  # price
    assert updated_quota_after_purchase[1] == 200  # amount (1200 - 1000)

    holder.update_buy_back_quota(100, 1000, {"from": operator, 'gas_price': 1950000000})
    holder.buy_back(1000, {"from": a[1], 'gas_price': 1950000000})
    assert holder.finance_shares(a[1]) == 0
    assert holder.total_finance_shares() == purchase_amount - 1000

def test_dividend():
    mock_token = Erc20.deploy(1000000 * 10**18, "Mock Token", 18, "MTK", {'from': a[0], 'gas_price': 1950000000})
    # Deploy the ShareHolder contract
    holder = ShareHolder.deploy(mock_token, {"from": a[0], 'gas_price': 1950000000})
    assert holder.get_shares(a[0]) == 10**20
    holder.vote_dilution_shares(10**17 * 10, {"from": a[0], 'gas_price': 1950000000})
    holder.dividend({"from": a[0], 'gas_price': 1950000000})
    holder.redistribute({"from": a[0], 'gas_price': 1950000000})

    # Add a contribution
    holder.submit_contribution(a[1], 10**17 * 10, {"from": a[0], 'gas_price': 1950000000})
    holder.update_finance_quota(100, 1000, {"from": a[0], 'gas_price': 1950000000})

    mint_amount = 10000 * 10**18
    mock_token.transfer(a[1], mint_amount, {"from": a[0], 'gas_price': 1950000000})
    mock_token.approve(holder.address, mint_amount, {"from": a[1], 'gas_price': 1950000000})

    purchase_amount = 1000
    holder.purchase_finance_shares(100, purchase_amount, {"from": a[1], 'gas_price': 1950000000})

    holder.dividend({"from": a[0], 'gas_price': 1950000000})
    holder.redistribute({"from": a[0], 'gas_price': 1950000000})

def test_update_buy_back_quota():
    operator = a[0]
    mock_token = Erc20.deploy(1000000 * 10**18, "Mock Token", 18, "MTK", {'from': a[0], 'gas_price': 1950000000})
    holder = ShareHolder.deploy(mock_token, {"from": operator, 'gas_price': 1950000000})

    holder.update_buy_back_quota(100, 1000, {"from": operator, 'gas_price': 1950000000})
    quota = holder.buyback_finance_quota()
    assert quota[0] == 100  # price
    assert quota[1] == 1000  # amount

    holder.update_buy_back_quota(100, 500, {"from": operator, 'gas_price': 1950000000})
    updated_quota = holder.buyback_finance_quota()
    assert updated_quota[0] == 100  # price
    assert updated_quota[1] == 1500  # amount (1000 + 500)

    holder.update_buy_back_quota(200, 2000, {"from": operator, 'gas_price': 1950000000})
    new_quota = holder.buyback_finance_quota()
    assert new_quota[0] == 200  # price
    assert new_quota[1] == 3500  # amount

    holder.update_buy_back_quota(200, -300, {"from": operator, 'gas_price': 1950000000})
    final_quota = holder.buyback_finance_quota()
    assert final_quota[0] == 200  # price
    assert final_quota[1] == 3200  # amount (3500 - 300)

def test_update_share_owner():
    operator = a[0]
    mock_token = Erc20.deploy(1000000 * 10**18, "Mock Token", 18, "MTK", {'from': a[0], 'gas_price': 1950000000})
    holder = ShareHolder.deploy(mock_token, {"from": a[0], 'gas_price': 1950000000})

    mint_amount = 10000 * 10**18
    mock_token.transfer(a[1], mint_amount, {"from": a[0], 'gas_price': 1950000000})
    mock_token.approve(holder.address, mint_amount, {"from": a[1], 'gas_price': 1950000000})

    purchase_amount = 1000
    holder.update_finance_quota(100, 2000, {"from": a[0], 'gas_price': 1950000000})
    holder.purchase_finance_shares(100, purchase_amount, {"from": a[1], 'gas_price': 1950000000})
    assert holder.finance_shares(a[1]) == purchase_amount
    assert holder.total_finance_shares() == purchase_amount

    # Update the owner of the shares
    holder.update_finance_shares_owner(a[2], {"from": a[1], 'gas_price': 1950000000})
    assert holder.finance_shares(a[2]) == purchase_amount
    assert holder.finance_shares(a[1]) == 0

    holder.update_shares_owner(a[3], {"from": a[0], 'gas_price': 1950000000})
    assert holder.shares(a[3]) == 10 ** 20
    assert holder.shares(a[0]) == 0

def test_pay_to():
    operator = a[0]
    mock_token = Erc20.deploy(1000000 * 10**18, "Mock Token", 18, "MTK", {'from': a[0], 'gas_price': 1950000000})
    holder = ShareHolder.deploy(mock_token, {"from": a[0], 'gas_price': 1950000000})

    pay_amount = 1000 * 10**18
    mock_token.transfer(holder.address, pay_amount, {"from": a[0], 'gas_price': 1950000000})
    # Test pay_to function
    initial_balance = mock_token.balanceOf(a[3])
    holder.pay_to(a[3], pay_amount, {"from": a[0], 'gas_price': 1950000000})
    final_balance = mock_token.balanceOf(a[3])
    assert final_balance - initial_balance == pay_amount


def test_vote_operator():
    mock_token = Erc20.deploy(1000000 * 10**18, "Mock Token", 18, "MTK", {'from': a[0], 'gas_price': 1950000000})
    holder = ShareHolder.deploy(mock_token, {"from": a[0], 'gas_price': 1950000000})

    assert '0x0000000000000000000000000000000000000000' == holder.operator_votes(a[0])
    assert a[0] == holder.operator()

    holder.vote_operator(a[1], {"from": a[0], 'gas_price': 1950000000})
    assert a[1] == holder.operator_votes(a[0])
    assert a[1] == holder.operator()

def test_vote_dilution_shares():
    operator = a[0]
    mock_token = Erc20.deploy(1000000 * 10**18, "Mock Token", 18, "MTK", {'from': a[0], 'gas_price': 1950000000})
    holder = ShareHolder.deploy(mock_token, {"from": a[0], 'gas_price': 1950000000})

    holder.vote_dilution_shares(10**20/100*60, {"from": a[0], 'gas_price': 1950000000})
    assert 10**20/100*60 == holder.dilution_shares()

    holder.submit_contribution(a[1], 10**20/100 * 30, {"from": operator, 'gas_price': 1950000000})
    holder.submit_contribution(a[2], 10**20/100 * 30, {"from": operator, 'gas_price': 1950000000})
    holder.dividend({"from": operator, 'gas_price': 1950000000})
    holder.redistribute({"from": operator, 'gas_price': 1950000000})
    assert 10**20/100 * 30 == holder.shares(a[1])
    assert 10**20/100 * 30 == holder.shares(a[2])
