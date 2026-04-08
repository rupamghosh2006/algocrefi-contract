from algopy import ARC4Contract, Account, Global, LocalState, Txn, UInt64
from algopy.arc4 import abimethod


class AlgocrefiAura(ARC4Contract):

    def __init__(self) -> None:
        self.aura_earned = LocalState(UInt64, key="aura_earned")
        self.aura_penalty = LocalState(UInt64, key="aura_penalty")
        self.blacklisted = LocalState(UInt64, key="blacklisted")

    @abimethod(allow_actions=["OptIn"])
    def opt_in(self) -> None:
        self.aura_earned[Txn.sender] = UInt64(0)
        self.aura_penalty[Txn.sender] = UInt64(0)
        self.blacklisted[Txn.sender] = UInt64(0)

    @abimethod()
    def add_repayment_aura(self, user: Account, interest_paid: UInt64) -> UInt64:
        assert Txn.sender == Global.creator_address, "Only admin"
        self.aura_earned[user] = self.aura_earned.get(user, UInt64(0)) + interest_paid
        return self.get_net_aura(user)

    @abimethod()
    def add_default_penalty(self, user: Account, penalty: UInt64) -> UInt64:
        assert Txn.sender == Global.creator_address, "Only admin"
        self.aura_penalty[user] = self.aura_penalty.get(user, UInt64(0)) + penalty
        return self.get_net_aura(user)

    @abimethod()
    def blacklist_unsecured(self, user: Account) -> UInt64:
        assert Txn.sender == Global.creator_address, "Only admin"
        self.blacklisted[user] = UInt64(1)
        return self.blacklisted[user]

    @abimethod(readonly=True)
    def get_net_aura(self, user: Account) -> UInt64:
        earned = self.aura_earned.get(user, UInt64(0))
        penalty = self.aura_penalty.get(user, UInt64(0))
        if earned >= penalty:
            return earned - penalty
        return UInt64(0)

    @abimethod(readonly=True)
    def get_aura_earned(self, user: Account) -> UInt64:
        return self.aura_earned.get(user, UInt64(0))

    @abimethod(readonly=True)
    def get_aura_penalty(self, user: Account) -> UInt64:
        return self.aura_penalty.get(user, UInt64(0))

    @abimethod(readonly=True)
    def is_blacklisted(self, user: Account) -> UInt64:
        return self.blacklisted.get(user, UInt64(0))
