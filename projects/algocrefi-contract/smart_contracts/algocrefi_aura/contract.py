from algopy import ARC4Contract, UInt64
from algopy.arc4 import abimethod


class AlgocrefiAura(ARC4Contract):

    def __init__(self) -> None:
        self.total_supply = UInt64(0)

    @abimethod()
    def mint(self, amount: UInt64) -> None:
        self.total_supply += amount

    @abimethod()
    def burn(self, amount: UInt64) -> None:
        assert self.total_supply >= amount
        self.total_supply -= amount

    @abimethod()
    def get_total_supply(self) -> UInt64:
        return self.total_supply