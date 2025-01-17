// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// import "./console.sol";

interface IERC20 {
    function transfer(address _to, uint256 _value) external returns (bool success);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract ShareHolder {
    uint256 constant TOTAL_SHARES = 10**20;

    address public operator;
    mapping(address => address) public operator_votes;

    mapping(uint256 => address) public holders;
    uint256 next_holder_no = 1;

    mapping(address => uint256) public shares;
    uint256 public dilution_shares = 0;
    mapping(address => uint256) public dilution_shares_votes;

    uint256 public pay_to_limit = 0;
    uint256 public pay_to_amount = 0;
    mapping(address => uint256) public pay_to_limit_votes;

    uint256 public last_redistribute_timestamp = 0;
    bool can_dividend = true;
    event SharesIssued(address indexed holder, uint256 amount);
    // event SharesTransferred(address indexed from, address indexed to, uint256 amount);

    uint256 public total_finance_shares = 0;
    mapping(uint256 => address) public finance_holders;
    mapping(address => uint256) public finance_shares;
    uint256 next_finance_investor_no = 0;

    struct Quota {
        uint256 price;
        uint256 amount;
    }
    Quota[] public available_finance_quota;
    Quota public buyback_finance_quota;

    struct Contribution {
        address contributor;
        uint256 amount;
    }
    Contribution[] contributions;
    event ContributionAdded(address indexed contributor, uint256 amount);

    event FinanceSharesIssued(address indexed investor, uint256 percentage);
    // event FinanceSharesTransferred(address indexed investor);
    event FinanceSharesBuyback(address indexed investor, uint256 percentage);

    IERC20 public token;
    uint256 public fee;

    constructor(address _token_address) {
        operator = msg.sender;
        shares[msg.sender] = TOTAL_SHARES;
        holders[next_holder_no] = msg.sender;
        emit SharesIssued(msg.sender, TOTAL_SHARES);
        token = IERC20(_token_address);
        last_redistribute_timestamp = block.timestamp;
        fee = 0;
    }

    function get_shares(address _holder) public view returns (uint256) {
        return shares[_holder] * (TOTAL_SHARES - total_finance_shares) / TOTAL_SHARES;
    }

    function pay_to(address _user, uint256 _amount) public {
        require(msg.sender == address(operator), "operator required");
        require(pay_to_amount + _amount <= pay_to_limit, "pay_to_amount exceeds pay_to_limit");
        require(token.transfer(_user, _amount), "token transfer failed");
        pay_to_amount += _amount;
    }

    function submit_contribution(address _contributor, uint256 _amount) public {
        require(msg.sender == address(operator), "operator required");
        uint256 total_contribution = 0;
        for (uint256 i = 0; i < contributions.length; i++) {
            total_contribution += contributions[i].amount;
        }
        require(_amount + total_contribution <= dilution_shares, 'dilution shares over');

        contributions.push(Contribution(_contributor, _amount));
        emit ContributionAdded(_contributor, _amount);
    }

    function dividend() public {
        require(msg.sender == address(operator), "operator required");
        require(block.timestamp - last_redistribute_timestamp > 1, "wait for more time");
        require(can_dividend, "can dividend required");
        can_dividend = false;

        uint256 to_dividend = token.balanceOf(address(this));
        // console.log(to_dividend);
        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            address holder = holders[i];
            // console.log(holder);
            // console.log(shares[holder]);
            // console.log(TOTAL_SHARES - total_finance_shares);
            // console.log(to_dividend * shares[holder] * (TOTAL_SHARES - total_finance_shares) / TOTAL_SHARES / TOTAL_SHARES);
            token.transfer(holder, to_dividend * shares[holder] * (TOTAL_SHARES - total_finance_shares) / TOTAL_SHARES / TOTAL_SHARES);
        }
        // console.log(TOTAL_SHARES);
        // console.log(total_finance_shares);
        
        for (uint256 i = 1; i < next_finance_investor_no+1; i++) {
            // console.log(i);
            // console.log(finance_holders[i]);
            // console.log(finance_shares[finance_holders[i]]);
            // if(finance_holders[i] == msg.sender){
            //     // console.log(finance_shares[finance_holders[i]]);
            // }
        }
    }

    function redistribute() public {
        require(msg.sender == address(operator), "operator required");
        require(!can_dividend, "dividend first");
        last_redistribute_timestamp = block.timestamp;
        can_dividend = true;

        uint256 total_contribution = 0;
        for (uint256 i = 0; i < contributions.length; i++) {
            total_contribution += contributions[i].amount;
        }

        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            // console.log(shares[holders[i]]);
            // console.log(shares[holders[i]] * (TOTAL_SHARES - total_contribution) / TOTAL_SHARES);
            shares[holders[i]] = shares[holders[i]] * (TOTAL_SHARES - total_contribution) / TOTAL_SHARES;
        }

        for (uint256 i = 0; i < contributions.length; i++) {
            uint256 share = shares[contributions[i].contributor];
            shares[contributions[i].contributor] = share + contributions[i].amount;

            if (share == 0) {
                next_holder_no += 1;
                holders[next_holder_no] = contributions[i].contributor;
            }
        }

        for (uint256 i = 0; i < contributions.length; i++) {
            contributions.pop();
        }
    }

    function vote_operator(address _operator) public {
        require(shares[msg.sender] > 0, "voter must be a holder");
        operator_votes[msg.sender] = _operator;

        uint256 vote_shares = 0;
        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            address holder = holders[i];
            // console.log(holder);
            // console.log(operator_votes[holder]);
            // console.log(_operator);
            if(operator_votes[holder] == _operator){
                uint256 share = shares[holder];
                vote_shares += share;
                // console.log(vote_shares);
                if(vote_shares > TOTAL_SHARES/2){
                    operator = _operator;
                    break;
                }
            }
        }
    }

    function vote_dilution_shares(uint256 _amount) public {
        require(shares[msg.sender] > 0, "voter must be a holder");

        dilution_shares_votes[msg.sender] = _amount;
        uint256 voting_shares = 0;
        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            address holder = holders[i];
            // console.log(holder);
            if(dilution_shares_votes[holder] == _amount){
                voting_shares += shares[holder];
                if(voting_shares > TOTAL_SHARES/2){
                    dilution_shares = _amount;
                    break;
                }
            }

            // console.log(shares[holders[i]]);
        }
    }

    function vote_pay_to_limit(uint256 _amount) public {
        require(shares[msg.sender] > 0, "voter must be a holder");

        uint256 voting_shares = 0;
        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            address holder = holders[i];
            // console.log(holder);
            if(pay_to_limit_votes[holder] == _amount){
                voting_shares += shares[holder];
                if(voting_shares > TOTAL_SHARES/2){
                    pay_to_limit = _amount;
                    break;
                }
            }

            // console.log(shares[holders[i]]);
        }
    }

    function purchase_finance_shares(uint256 _price, uint256 _amount) public {
        bool quota_found = false;
        for (uint256 _i = 0; _i < available_finance_quota.length; _i++) {
            if (available_finance_quota[_i].price == _price) {
                uint256 _available_amount = available_finance_quota[_i].amount;
                uint256 _purchase_amount = _amount < _available_amount ? _amount : _available_amount;
                require(_purchase_amount > 0, "Insufficient quota");
                available_finance_quota[_i].amount -= _purchase_amount;
                quota_found = true;
                break;
            }
        }
        require(quota_found, "no matching quota found");

        uint256 _total_cost = _price * _amount;
        require(token.transferFrom(msg.sender, address(this), _total_cost), "token transfer failed");

        if (finance_shares[msg.sender] == 0) {
            next_finance_investor_no += 1;
            finance_holders[next_finance_investor_no] = msg.sender;
        }
        finance_shares[msg.sender] += _amount;
        total_finance_shares += _amount;
    }

    function buy_back(uint256 _amount) public {
        finance_shares[msg.sender] -= _amount;
        total_finance_shares -= _amount;

        require(token.transfer(msg.sender, buyback_finance_quota.price * _amount), "token transfer failed");
    }

    function update_finance_shares_owner(address _owner) public {
        for (uint256 i = 1; i < next_finance_investor_no+1; i++) {
            // console.log(i);
            if(finance_holders[i] == msg.sender){
                finance_holders[i] = _owner;
                // console.log(finance_shares[finance_holders[i]]);
            }
        }

        uint256 share = finance_shares[msg.sender];
        delete finance_shares[msg.sender];
        finance_shares[_owner] = share;
    }

    function update_shares_owner(address _owner) public {
        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            if(holders[i] == msg.sender){
                holders[i] = _owner;
                // console.log(shares[holders[i]]);
            }
        }

        uint256 share = shares[msg.sender];
        delete shares[msg.sender];
        shares[_owner] = share;
    }

    function update_finance_quota(uint256 price, int256 amount) public {
        require(msg.sender == operator, "operator required");

        bool found = false;
        for (uint256 i = 0; i < available_finance_quota.length; i++) {
            if (available_finance_quota[i].price == price) {
                if (amount > 0){
                    available_finance_quota[i].amount += uint256(amount);
                }else{
                    available_finance_quota[i].amount -= uint256(-amount);
                }
                found = true;
            }
        }

        if (!found && amount > 0){
            available_finance_quota.push(Quota(price, uint256(amount)));
        }
    }

    function update_buy_back_quota(uint256 _price, int256 _amount) public {
        require(msg.sender == address(operator), "operator required");
        if(_amount > 0){
            buyback_finance_quota.amount += uint256(_amount);
        }else{
            buyback_finance_quota.amount -= uint256(-_amount);
        }
        buyback_finance_quota.price = _price;
    }

    function update_fee(uint256 _fee) public {
        require(msg.sender == operator, "operator required");
        fee = _fee;
    }
}
