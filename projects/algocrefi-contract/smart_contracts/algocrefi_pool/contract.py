from algopy import ARC4Contract, UInt64, Global, BoxMap, Account
from algopy.arc4 import abimethod


class AlgocrefiPool(ARC4Contract):

    def __init__(self) -> None:
        self.total_shares = UInt64(0)
        self.pool = UInt64(0)
        self.shares: BoxMap[Account, UInt64] = BoxMap(Account, UInt64)

    @abimethod()
    def deposit(self, amount: UInt64) -> UInt64:
        assert amount > 0, "Amount must be positive"
        
        sender = Global.caller_application_address
        
        if self.pool == 0 or self.total_shares == 0:
            self.pool += amount
            self.total_shares += amount
            self.shares[sender] = self.shares[sender] + amount
            return amount
        
        shares_to_mint = (amount * self.total_shares) // self.pool
        
        assert shares_to_mint > 0, "Amount too small"
        
        self.pool += amount
        self.total_shares += shares_to_mint
        self.shares[sender] = self.shares[sender] + shares_to_mint
        
        return shares_to_mint

    @abimethod()
    def withdraw(self, share_amount: UInt64) -> UInt64:
        sender = Global.caller_application_address
        
        user_shares = self.shares[sender]
        assert user_shares >= share_amount, "Insufficient shares"
        
        algo_to_return = (share_amount * self.pool) // self.total_shares
        assert algo_to_return > 0, "Nothing to withdraw"
        
        self.pool -= algo_to_return
        self.shares[sender] = user_shares - share_amount
        self.total_shares -= share_amount
        
        return algo_to_return

    @abimethod()
    def get_pool(self) -> UInt64:
        return self.pool

    @abimethod()
    def get_shares(self, address: Account) -> UInt64:
        return self.shares[address]

    @abimethod()
    def get_total_shares(self) -> UInt64:
        return self.total_shares

    @abimethod()
    def get_share_price(self) -> UInt64:
        if self.total_shares == 0:
            return UInt64(0)
        return self.pool // self.total_shares
