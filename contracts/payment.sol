// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// import "./console.sol";

interface IERC20 {
    function transfer(address _to, uint256 _value) external returns (bool success);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

contract BulletPay {
    IERC20 public token;
    uint256 public next_account_id;

    struct Topup {
        address spender;
        uint256 balance;
    }

    mapping(uint256 => Topup) public accounts;

    constructor(address _token_address) {
        token = IERC20(_token_address);
        next_account_id = 1;
    }

    function recover_signer(bytes32 _message_hash, bytes memory _signature) internal view returns (address) {
        bytes32 r;
        bytes32 s;
        uint8 v;

        require(_signature.length == 65, "Invalid signature length");

        assembly {
            r := mload(add(_signature, 32))
            s := mload(add(_signature, 64))
            v := byte(0, mload(add(_signature, 96)))
        }

        if (v < 27) {
            v += 27;
        }

        address recoveredAddress = ecrecover(_message_hash, v, r, s);
        require(recoveredAddress != address(0), "Invalid signature2");
    
        return recoveredAddress;
    }
}
