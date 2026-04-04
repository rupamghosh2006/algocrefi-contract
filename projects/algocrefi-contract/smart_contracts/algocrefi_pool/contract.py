from algopy import ARC4Contract, UInt64, Global, Txn, Box, GlobalState, Bytes
from algopy.arc4 import abimethod


class AlgocrefiPool(ARC4Contract):

    def __init__(self) -> None:
        self.pool = GlobalState(UInt64, key="pool")
        self.total_shares = GlobalState(UInt64, key="total_shares")

    @abimethod()
    def deposit(self, amount: UInt64) -> UInt64:
        sender = Txn.sender
        
        pool_val = self.pool.get(UInt64(0))
        total_val = self.total_shares.get(UInt64(0))
        
        if pool_val == 0:
            minted = amount
        else:
            minted = (amount * total_val) // pool_val

        self.pool.value = pool_val + amount
        self.total_shares.value = total_val + minted
        
        box_key = Bytes(b"s") + sender.bytes[:31]
        user_box = Box(UInt64, key=box_key)
        user_box.create(size=UInt64(8))
        current_shares = user_box.get(default=UInt64(0))
        user_box.value = current_shares + minted

        return minted

    @abimethod()
    def withdraw(self, shares: UInt64) -> UInt64:
        sender = Txn.sender
        
        box_key = Bytes(b"s") + sender.bytes[:31]
        user_box = Box(UInt64, key=box_key)
        user_shares = user_box.get(default=UInt64(0))
        
        assert user_shares >= shares, "Insufficient shares"

        pool_val = self.pool.get(UInt64(0))
        total_val = self.total_shares.get(UInt64(0))
        
        algo = (shares * pool_val) // total_val

        self.pool.value = pool_val - algo
        self.total_shares.value = total_val - shares
        user_box.value = user_shares - shares

        return algo

    @abimethod(readonly=True)
    def get_pool(self) -> UInt64:
        return self.pool.get(UInt64(0))

    @abimethod(readonly=True)
    def get_total_shares(self) -> UInt64:
        return self.total_shares.get(UInt64(0))

    @abimethod(readonly=True)
    def get_shares(self, address: Bytes) -> UInt64:
        box_key = Bytes(b"s") + address[:31]
        user_box = Box(UInt64, key=box_key)
        return user_box.get(default=UInt64(0))
