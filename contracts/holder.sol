// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// import "./console.sol";

interface IERC20 {
    function transfer(address _to, uint256 _value) external returns (bool success);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    //function balanceOf(address account) external view returns (uint256);
}

contract ShareHolder {
    uint256 constant total_shares = 10**20;
    address public operator;

    mapping(uint256 => address) public holders;
    mapping(address => uint256) public shares;
    mapping(address => address) public votes;
    uint256 next_holder_no = 1;

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

    event FinanceInvestorSharesIssued(address indexed investor, uint256 percentage);
    event FinanceInvestorSharesTransferred(address indexed investor);
    event FinanceInvestorSharesBuyback(address indexed investor, uint256 percentage);

    IERC20 public token;
    uint256 public proportion = 10000;

    constructor(address _tokenAddress) {
        operator = msg.sender;
        shares[msg.sender] = total_shares;
        holders[next_holder_no] = msg.sender;
        emit SharesIssued(msg.sender, total_shares);
        token = IERC20(_tokenAddress);
    }

    function submit_contribution(address _contributor, uint256 _amount) public {
        require(msg.sender == address(operator), "operator required");
        contributions.push(Contribution(_contributor, _amount));
        emit ContributionAdded(_contributor, _amount);
    }

    function get_shares(address _holder) public view returns (uint256) {
        return shares[_holder] * (total_shares - total_finance_shares) / total_shares;
    }

    function dividend() public {
        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            address holder = holders[i];
            // console.log(holder);
            // console.log(shares[holders[i]]);
            // console.log(shares[holders[i]] * (total_shares - total_finance_shares) / total_finance_shares);
        }
        // console.log(total_shares);
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

        uint256 total_contribution = 0;
        for (uint256 i = 0; i < contributions.length; i++) {
            total_contribution += contributions[i].amount;
        }

        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            // console.log(shares[holders[i]]);
            // console.log(shares[holders[i]] * (total_shares - total_contribution) / total_shares);
            shares[holders[i]] = shares[holders[i]] * (total_shares - total_contribution) / total_shares;
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

    function purchase_finance_shares(uint256 _price, uint256 _amount) public {
        bool _quota_found = false;
        for (uint256 _i = 0; _i < available_finance_quota.length; _i++) {
            if (available_finance_quota[_i].price == _price) {
                uint256 _available_amount = available_finance_quota[_i].amount;
                uint256 _purchase_amount = _amount < _available_amount ? _amount : _available_amount;
                require(_purchase_amount > 0, "Insufficient quota");
                available_finance_quota[_i].amount -= _purchase_amount;
                _quota_found = true;
                break;
            }
        }
        require(_quota_found, "No matching quota found");

        uint256 _total_cost = _price * _amount;
        require(token.transferFrom(msg.sender, address(this), _total_cost), "Token transfer failed");

        if (finance_shares[msg.sender] == 0) {
            next_finance_investor_no += 1;
            finance_holders[next_finance_investor_no] = msg.sender;
        }
        finance_shares[msg.sender] += _amount;
        total_finance_shares += _amount;
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

    function pay_to(address _user, uint256 _amount) public {
        require(msg.sender == address(operator), "operator required");
        require(token.transfer(_user, _amount), "Token transfer failed");
    }

    function set_proportion(uint256 _proportion) public {
        require(msg.sender == address(operator), "operator required");
        proportion = _proportion;
    }

    function buy_back(uint256 _amount) public {
        finance_shares[msg.sender] -= _amount;
        total_finance_shares -= _amount;

        require(token.transfer(msg.sender, buyback_finance_quota.price * _amount), "Token transfer failed");
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

    function vote_operator(address _operator) public {
        votes[msg.sender] = _operator;

        uint256 vote_shares = 0;
        for (uint256 i = 1; i < next_holder_no+1; i++) {
            // console.log(i);
            address holder = holders[i];
            // console.log(holder);
            // console.log(votes[holder]);
            // console.log(_operator);
            if(votes[holder] == _operator){
                uint256 share = shares[holder];
                vote_shares += share;
                // console.log(vote_shares);
                if(vote_shares > total_shares/2){
                    operator = _operator;
                    break;
                }
            }
        }
    }
}
