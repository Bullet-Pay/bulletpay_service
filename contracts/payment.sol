// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// import "./console.sol";

interface IERC20 {
    function transfer(address _to, uint256 _value) external returns (bool success);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

contract BulletPay {
    IERC20 public token;
    uint256 public total;
    uint256 public next_topup_id;

    struct Topup {
        address spender;
        uint256 balance;
    }

    mapping(uint256 => Topup) public topups;

    event TopupCreated(uint256 indexed topup_id, address indexed spender, uint256 amount);
    event TopupSpent(uint256 indexed topup_id, address indexed spender, uint256 remaining_balance);

    constructor(address _token_address) {
        token = IERC20(_token_address);
        next_topup_id = 1;
    }

    function topup(uint256 _amount, address _spender) external {
        require(_amount >= 10**6, "deposit amount must be greater than one dollor");

        topups[next_topup_id] = Topup({
            spender: _spender,
            balance: _amount
        });
        require(token.transferFrom(msg.sender, address(this), _amount), "transfer failed");
        emit TopupCreated(next_topup_id, _spender, _amount);
        total += _amount;
        next_topup_id++;
    }

    function pay_to(uint256 _from_topup_id, address _to_address, uint256 _amount, bytes memory _signature) external {
        require(topups[_from_topup_id].balance >= _amount, "insufficient balance");
        bytes memory encoded = abi.encodePacked(_to_address, _amount);
        // console.logBytes(encoded);

        bytes32 hash1 = keccak256(encoded);
        // console.logBytes32(hash1);
        bytes32 hash2 = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", hash1));
        // console.logBytes32(hash2);

        // console.logAddress(topups[_from_topup_id].spender);
        address signer = recover_signer(hash2, _signature);
        // console.logAddress(signer);
        require(signer == topups[_from_topup_id].spender, "invalid signature1");

        uint256 remaining_balance = topups[_from_topup_id].balance - _amount;
        topups[_from_topup_id].balance = remaining_balance;

        // console.logAddress(_to_address);
        // console.log(_amount);

        require(token.transfer(_to_address, _amount), "transfer to address failed");
        total -= _amount;
        // console.logAddress(signer);
        // console.log(remaining_balance);

        emit TopupSpent(_from_topup_id, signer, remaining_balance);
    }

    function recover_signer(bytes32 _message_hash, bytes memory _signature) internal view returns (address) {
        bytes32 r;
        bytes32 s;
        uint8 v;

        require(_signature.length == 65, "invalid signature length");

        assembly {
            r := mload(add(_signature, 32))
            s := mload(add(_signature, 64))
            v := byte(0, mload(add(_signature, 96)))
        }

        if (v < 27) {
            v += 27;
        }

        address recoveredAddress = ecrecover(_message_hash, v, r, s);
        require(recoveredAddress != address(0), "invalid signature2");
    
        return recoveredAddress;
    }
}
