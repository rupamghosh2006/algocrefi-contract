from algopy import ARC4Contract, Account, Asset, Global, LocalState, Txn, UInt64, gtxn, itxn
from algopy.arc4 import abimethod


class AlgocrefiLending(ARC4Contract):

    def __init__(self) -> None:
        self.available_algo = UInt64(0)
        self.usdc_asset_id = UInt64(10458941)
        self.daily_interest_bps = UInt64(10)  # 0.10% per day

        self.loan_active = LocalState(UInt64, key="loan_active")
        self.loan_type = LocalState(UInt64, key="loan_type")  # 1=collateral, 2=unsecured
        self.principal = LocalState(UInt64, key="principal")
        self.interest_due = LocalState(UInt64, key="interest_due")
        self.due_amount = LocalState(UInt64, key="due_amount")
        self.collateral_usdc = LocalState(UInt64, key="collateral_usdc")
        self.due_ts = LocalState(UInt64, key="due_ts")

        self.aura_earned = LocalState(UInt64, key="aura_earned")
        self.aura_penalty = LocalState(UInt64, key="aura_penalty")
        self.aura_blacklisted = LocalState(UInt64, key="aura_blacklisted")

    @abimethod(allow_actions=["OptIn"])
    def opt_in(self) -> None:
        self.loan_active[Txn.sender] = UInt64(0)
        self.loan_type[Txn.sender] = UInt64(0)
        self.principal[Txn.sender] = UInt64(0)
        self.interest_due[Txn.sender] = UInt64(0)
        self.due_amount[Txn.sender] = UInt64(0)
        self.collateral_usdc[Txn.sender] = UInt64(0)
        self.due_ts[Txn.sender] = UInt64(0)
        self.aura_earned[Txn.sender] = UInt64(0)
        self.aura_penalty[Txn.sender] = UInt64(0)
        self.aura_blacklisted[Txn.sender] = UInt64(0)

    @abimethod()
    def app_opt_in_usdc(self) -> None:
        assert Txn.sender == Global.creator_address, "Only admin"

        itxn.AssetTransfer(
            xfer_asset=self.usdc_asset_id,
            asset_receiver=Global.current_application_address,
            asset_amount=UInt64(0),
            fee=UInt64(0),
        ).submit()

    @abimethod()
    def add_liquidity(self, payment_txn_index: UInt64) -> UInt64:
        pay = gtxn.PaymentTransaction(payment_txn_index)
        assert pay.sender == Txn.sender, "Invalid liquidity sender"
        assert pay.receiver == Global.current_application_address, "Invalid receiver"
        assert pay.amount > 0, "Liquidity must be positive"

        self.available_algo += pay.amount
        return self.available_algo

    @abimethod()
    def request_collateral_loan(
        self,
        algo_amount: UInt64,
        days_to_repay: UInt64,
        min_collateral_usdc: UInt64,
        collateral_txn_index: UInt64,
    ) -> UInt64:
        assert algo_amount > 0, "Amount must be positive"
        assert days_to_repay > 0, "Days must be positive"
        assert self.loan_active.get(Txn.sender, UInt64(0)) == 0, "Active loan exists"
        assert self.available_algo >= algo_amount, "Insufficient liquidity"

        collateral_txn = gtxn.AssetTransferTransaction(collateral_txn_index)
        assert collateral_txn.sender == Txn.sender, "Invalid collateral sender"
        assert collateral_txn.asset_receiver == Global.current_application_address, "Invalid collateral receiver"
        assert collateral_txn.xfer_asset == Asset(self.usdc_asset_id), "Invalid collateral asset"
        assert collateral_txn.asset_amount >= min_collateral_usdc, "Insufficient collateral"

        per_day_interest = (algo_amount * self.daily_interest_bps) // UInt64(10_000)
        interest = per_day_interest * days_to_repay
        due = algo_amount + interest

        self.loan_active[Txn.sender] = UInt64(1)
        self.loan_type[Txn.sender] = UInt64(1)
        self.principal[Txn.sender] = algo_amount
        self.interest_due[Txn.sender] = interest
        self.due_amount[Txn.sender] = due
        self.collateral_usdc[Txn.sender] = collateral_txn.asset_amount
        self.due_ts[Txn.sender] = Global.latest_timestamp + (days_to_repay * UInt64(86_400))

        self.available_algo -= algo_amount

        itxn.Payment(
            receiver=Txn.sender,
            amount=algo_amount,
            fee=UInt64(0),
        ).submit()

        return due

    @abimethod()
    def request_unsecured_loan(self, algo_amount: UInt64, days_to_repay: UInt64) -> UInt64:
        assert algo_amount > 0, "Amount must be positive"
        assert days_to_repay > 0, "Days must be positive"
        assert self.loan_active.get(Txn.sender, UInt64(0)) == 0, "Active loan exists"
        assert self.available_algo >= algo_amount, "Insufficient liquidity"
        assert self.aura_blacklisted.get(Txn.sender, UInt64(0)) == 0, "Blacklisted for unsecured loans"
        assert self.aura_earned.get(Txn.sender, UInt64(0)) > self.aura_penalty.get(Txn.sender, UInt64(0)), "AURA too low"

        per_day_interest = (algo_amount * self.daily_interest_bps) // UInt64(10_000)
        interest = per_day_interest * days_to_repay
        due = algo_amount + interest

        self.loan_active[Txn.sender] = UInt64(1)
        self.loan_type[Txn.sender] = UInt64(2)
        self.principal[Txn.sender] = algo_amount
        self.interest_due[Txn.sender] = interest
        self.due_amount[Txn.sender] = due
        self.collateral_usdc[Txn.sender] = UInt64(0)
        self.due_ts[Txn.sender] = Global.latest_timestamp + (days_to_repay * UInt64(86_400))

        self.available_algo -= algo_amount

        itxn.Payment(
            receiver=Txn.sender,
            amount=algo_amount,
            fee=UInt64(0),
        ).submit()

        return due

    @abimethod()
    def repay(self, payment_txn_index: UInt64) -> UInt64:
        assert self.loan_active.get(Txn.sender, UInt64(0)) == 1, "No active loan"

        due = self.due_amount.get(Txn.sender, UInt64(0))
        interest = self.interest_due.get(Txn.sender, UInt64(0))
        collateral = self.collateral_usdc.get(Txn.sender, UInt64(0))

        pay = gtxn.PaymentTransaction(payment_txn_index)
        assert pay.sender == Txn.sender, "Invalid repayment sender"
        assert pay.receiver == Global.current_application_address, "Invalid repayment receiver"
        assert pay.amount >= due, "Repayment too low"

        self.available_algo += due
        self.aura_earned[Txn.sender] = self.aura_earned.get(Txn.sender, UInt64(0)) + interest

        if collateral > 0:
            itxn.AssetTransfer(
                xfer_asset=self.usdc_asset_id,
                asset_receiver=Txn.sender,
                asset_amount=collateral,
                fee=UInt64(0),
            ).submit()

        self.loan_active[Txn.sender] = UInt64(0)
        self.loan_type[Txn.sender] = UInt64(0)
        self.principal[Txn.sender] = UInt64(0)
        self.interest_due[Txn.sender] = UInt64(0)
        self.due_amount[Txn.sender] = UInt64(0)
        self.collateral_usdc[Txn.sender] = UInt64(0)
        self.due_ts[Txn.sender] = UInt64(0)

        return due

    @abimethod()
    def liquidate_default(self, borrower: Account) -> UInt64:
        assert Txn.sender == Global.creator_address, "Only admin"
        assert self.loan_active.get(borrower, UInt64(0)) == 1, "No active loan"
        assert Global.latest_timestamp > self.due_ts.get(borrower, UInt64(0)), "Loan not overdue"

        loan_type = self.loan_type.get(borrower, UInt64(0))
        interest = self.interest_due.get(borrower, UInt64(0))
        collateral = self.collateral_usdc.get(borrower, UInt64(0))

        self.aura_penalty[borrower] = self.aura_penalty.get(borrower, UInt64(0)) + interest

        if loan_type == 2:
            self.aura_blacklisted[borrower] = UInt64(1)

        if collateral > 0:
            itxn.AssetTransfer(
                xfer_asset=self.usdc_asset_id,
                asset_receiver=Global.creator_address,
                asset_amount=collateral,
                fee=UInt64(0),
            ).submit()

        self.loan_active[borrower] = UInt64(0)
        self.loan_type[borrower] = UInt64(0)
        self.principal[borrower] = UInt64(0)
        self.interest_due[borrower] = UInt64(0)
        self.due_amount[borrower] = UInt64(0)
        self.collateral_usdc[borrower] = UInt64(0)
        self.due_ts[borrower] = UInt64(0)

        return interest

    @abimethod(readonly=True)
    def get_available_algo(self) -> UInt64:
        return self.available_algo

    @abimethod(readonly=True)
    def get_active_loan(self, borrower: Account) -> UInt64:
        return self.loan_active.get(borrower, UInt64(0))

    @abimethod(readonly=True)
    def get_due_amount(self, borrower: Account) -> UInt64:
        return self.due_amount.get(borrower, UInt64(0))

    @abimethod(readonly=True)
    def get_due_ts(self, borrower: Account) -> UInt64:
        return self.due_ts.get(borrower, UInt64(0))

    @abimethod(readonly=True)
    def get_aura_earned(self, borrower: Account) -> UInt64:
        return self.aura_earned.get(borrower, UInt64(0))

    @abimethod(readonly=True)
    def get_aura_penalty(self, borrower: Account) -> UInt64:
        return self.aura_penalty.get(borrower, UInt64(0))

    @abimethod(readonly=True)
    def is_blacklisted(self, borrower: Account) -> UInt64:
        return self.aura_blacklisted.get(borrower, UInt64(0))
