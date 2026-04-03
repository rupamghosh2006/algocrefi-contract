from algopy import ARC4Contract, UInt64
from algopy.arc4 import abimethod


class AlgocrefiLending(ARC4Contract):

    def __init__(self) -> None:
        self.loan = UInt64(0)
        self.collateral = UInt64(0)

    @abimethod()
    def borrow(self, amount: UInt64, collateral_amount: UInt64) -> None:
        # simple rule
        assert collateral_amount >= amount

        self.loan = amount
        self.collateral = collateral_amount

    @abimethod()
    def repay(self, amount: UInt64) -> None:
        assert amount >= self.loan

        self.loan = UInt64(0)
        self.collateral = UInt64(0)

    @abimethod()
    def get_loan(self) -> UInt64:
        return self.loan