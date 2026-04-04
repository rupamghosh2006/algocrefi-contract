from algopy import ARC4Contract, UInt64, Txn, LocalState
from algopy.arc4 import abimethod


class AlgoPool(ARC4Contract):

    def __init__(self) -> None:
        self.pool = UInt64(0)
        self.total_shares = UInt64(0)
        self.shares = LocalState(UInt64, key="shares")

    @abimethod()
    def opt_in(self) -> bool:
        self.shares[Txn.sender] = UInt64(0)
        return True

    @abimethod()
    def deposit(self, amount: UInt64) -> UInt64:
        user_shares = self.shares.get(Txn.sender, UInt64(0))

        if self.pool == 0:
            minted = amount
        else:
            minted = (amount * self.total_shares) // self.pool

        self.pool += amount
        self.total_shares += minted
        self.shares[Txn.sender] = user_shares + minted

        return minted

    @abimethod()
    def withdraw(self, share_amount: UInt64) -> UInt64:
        user_shares = self.shares.get(Txn.sender, UInt64(0))
        assert user_shares >= share_amount, "Insufficient shares"

        algo = (share_amount * self.pool) // self.total_shares

        self.pool -= algo
        self.total_shares -= share_amount
        self.shares[Txn.sender] = user_shares - share_amount

        return algo

    @abimethod(readonly=True)
    def get_pool(self) -> UInt64:
        return self.pool

    @abimethod(readonly=True)
    def get_total_shares(self) -> UInt64:
        return self.total_shares
