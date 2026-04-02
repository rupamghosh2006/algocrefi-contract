from algopy import ARC4Contract, UInt64
from algopy.arc4 import abimethod


class AlgocrefiPool(ARC4Contract):

    def __init__(self) -> None:
        self.pool = UInt64(0)

    @abimethod()
    def deposit(self, amount: UInt64) -> None:
        self.pool += amount

    @abimethod()
    def get_pool(self) -> UInt64:
        return self.pool
