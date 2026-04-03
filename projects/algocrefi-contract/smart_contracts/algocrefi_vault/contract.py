from algopy import ARC4Contract, UInt64
from algopy.arc4 import abimethod


class AlgocrefiVault(ARC4Contract):

    def __init__(self) -> None:
        self.total_balance = UInt64(0)

    @abimethod()
    def deposit(self, amount: UInt64) -> None:
        self.total_balance += amount

    @abimethod()
    def withdraw(self, amount: UInt64) -> None:
        assert self.total_balance >= amount
        self.total_balance -= amount

    @abimethod()
    def get_total_balance(self) -> UInt64:
        return self.total_balance