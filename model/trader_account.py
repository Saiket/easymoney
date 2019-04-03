"""Defines `TraderAccount` and supporting classes."""


__copyright__ = 'Copyright © 2019, Erik Anderson, James Abernathy, and Tyler Gerritsen'
__license__ = 'MIT'


import collections
import typing

# Local package imports at end of file to resolve circular dependencies




class FrozenError(ValueError):
    """An exception raised when attempting to buy or sell with this account
    after it was frozen.
    """

    def __init__(self
    ) -> None:
        super().__init__('Trader cannot trade using a frozen account.')


class InsufficientBalanceError(ValueError):
    """An exception raised when attempting to buy stock shares (or pay a
    sale trading fee) than this trader's account can't afford.
    """

    stock_symbol: str
    """The stock symbol that a `Trader` attempted to trade."""

    cost: float
    """The cost of `stock_symbol` that was too expensive."""

    balance: float
    """The `Trader`'s insufficient balance."""

    def __init__(self,
        stock_symbol: str,
        cost: float,
        balance: float
    ) -> None:
        self.stock_symbol = stock_symbol
        self.cost = cost
        self.balance = balance
        super().__init__(
            "Trader with ${:.2f} can't afford ${:.2f} charge for {!r} stock.".format(
                balance, cost, stock_symbol))


class InsufficientStockSharesError(ValueError):
    """An exception raised when attempting to sell more stock shares than this
    trader's account currently holds.
    """

    stock_symbol: str
    """The stock symbol that a `Trader` attempted to sell."""

    shares: float
    """The invalid quantity of shares that was greater than `shares_owned`."""

    shares_owned: float
    """The `Trader`'s owned quantity of `stock_symbol`."""

    def __init__(self,
        stock_symbol: str,
        shares: float,
        shares_owned: float
    ) -> None:
        self.stock_symbol = stock_symbol
        self.shares = shares
        self.shares_owned = shares_owned
        super().__init__(
            'Trader attempted to sell {:.2f} shares of {!r} stock, but only owns {:.2f}.'.format(
                shares, stock_symbol, shares_owned))


class StockShareQuantityError(ValueError):
    """An exception raised when attempting to buy or sell an invalid
    non-positive quantity of stock shares.
    """

    stock_symbol: str
    """The stock symbol that a `Trader` attempted to trade."""

    shares: float
    """The non-positive stock share quantity that was provided."""

    def __init__(self,
        stock_symbol: str,
        shares: float
    ) -> None:
        self.stock_symbol = stock_symbol
        self.shares = shares
        super().__init__(
            'Trader attempted to trade an invalid non-positive {!r} stock quantity {:.2f}.'.format(
                shares, stock_symbol))




class TraderAccount(object):
    """The bank balance and stock portfolio of an owning `Trader`, tied to a
    particular `StockMarket`. The account provides methods for traders to buy
    and sell their stocks, and statistics collection for later analysis.

    If a trader encounters an exception, or violates simulation rules, it gets
    frozen and cannot make any more trades. The following violations will
    freeze an account: selling unowned stock shares, or buying unaffordable
    stock shares. Accounts can also be manually frozen. Frozen accounts are
    effectively excluded from the simulation, and so traders must create new
    accounts if they need to continue participating.
    """


    _stock_market: 'StockMarket'
    """The market that this account consults to check prices."""

    _trader: 'Trader'
    """The trader that created and controls this account."""

    _balance_initial: float
    """The non-negative starting bank account balance of this account that was
    configured for the owning `_trader` at account creation.
    """

    _balance: float
    """The non-negative bank account balance of this account, in the same
    currency as `_stock_market`'s price data.
    """

    _stocks: typing.DefaultDict[str, float]
    """A `collections.defaultdict` of owned stock symbols mapped to
    non-negative quantities owned, defaulting to `0.0` for new keys.
    """

    _frozen: bool
    """When `True`, this account can no longer be used to `buy` or `sell`."""

    #TODO: Events:
    #   TRADER_ACCOUNT_BOUGHT
    #   TRADER_ACCOUNT_FROZEN
    #   TRADER_ACCOUNT_SOLD
    #   TRADER_ACCOUNT_UPDATED


    def __init__(self,
        market: 'StockMarket',
        trader: 'Trader'
    ) -> None:
        """Initialize this account with `trader`'s configured initial funds.
        All future `buy`ing and `sell`ing occurs on `market`.
        """
        self._stock_market = market
        self._trader = trader

        self._balance_initial = trader.get_initial_balance()
        self._balance = self._balance_initial
        self._stocks = collections.defaultdict(float)  # Default to 0.0
        self._frozen = False


    def get_stock_market(self
    ) -> 'StockMarket':
        """Return the market that this account consults for prices."""
        return self._stock_market

    def get_trader(self
    ) -> 'Trader':
        """Return the trader that created this account and owns its contents.
        """
        return self._trader


    def get_balance(self
    ) -> float:
        """Return this account's current bank balance, in the same unit of
        currency as `_stock_market`. This value is always non-negative.

        This result changes upon `TRADER_ACCOUNT_UPDATED` events.
        """
        return self._balance

    def get_stocks(self
    ) -> typing.Dict[str, float]:
        """Return the quantities of stock shares that this account holds as a
        `dict` mapping stock symbols to non-negative quantities.

        This result changes upon `TRADER_ACCOUNT_UPDATED` events.
        """
        return self._stocks.copy()


    def is_frozen(self
    ) -> bool:
        """Return `True` if this account has been frozen and can no longer
        `buy` or `sell` stocks. See the class' documentation for a description
        of the frozen state and why accounts freeze.

        This result changes upon `TRADER_ACCOUNT_FROZEN` events.
        """
        return self._frozen

    def freeze(self,
        reason: typing.Optional[str] = None,
        exception: typing.Optional[Exception] = None
    ) -> None:
        """Stops this account's trader from further `buy`ing or `sell`ing. An
        account cannot be unfrozen; its trader must instead create a new
        account.

        A brief `reason` sentence can be provided to be displayed to the user,
        optionally with the offending `exception`.

        Triggers `TRADER_ACCOUNT_FROZEN` if successful.
        """
        if self.is_frozen():
            return

        self._frozen = True
        #TODO: Broadcast TRADER_ACCOUNT_FROZEN


    def buy(self,
        stock_symbol: str,
        shares: float
    ) -> None:
        """Buy a quantity `shares` of `stock_symbol` at the current `_market`
        price, deducting from this account's balance and adding to its stock
        portfolio. The account must not be frozen; Buying with a frozen account
        raises `FrozenError`.

        The given `stock_symbol` must exist within `_market`. If it doesn't,
        this method raises `stock_market.StockSymbolUnrecognizedError`.

        The quantity `shares` to buy must be positive; If `shares` is zero or
        less, this raises `StockShareQuantityError`. If the cost to buy
        `shares` from `_market` plus the owning trader's trading fee is greater
        than this account's balance, `InsufficientBalanceError` is raised.

        Triggers `TRADER_ACCOUNT_BOUGHT` and `TRADER_ACCOUNT_UPDATED` if
        successful.
        """
        if self.is_frozen():
            raise FrozenError()

        if shares <= 0:
            raise StockShareQuantityError(stock_symbol, shares)

        price_per_share = self._market.get_stock_symbol_price(stock_symbol)
        cost = shares * price_per_share + self._trader.get_trading_fee()
        if cost > self.get_balance():
            raise InsufficientBalanceError(
                stock_symbol, cost, self.get_balance())

        # Make transaction
        self._balance -= cost
        self._stocks[stock_symbol] += shares
        #TODO: Broadcast TRADER_ACCOUNT_BOUGHT
        #TODO: Broadcast TRADER_ACCOUNT_UPDATED

    def sell(self,
        stock_symbol: str,
        shares: float
    ) -> None:
        """Sell a quantity `shares` of `stock_symbol` from this account at the
        `_market`'s current prices, exchanging those shares for a deposit into
        this account's balance minus the trader's trading fee. The account must
        not be frozen; Selling with a frozen account raises `FrozenError`.

        The given `stock_symbol` must exist within `_market`; Unrecognized
        stock symbols raise `stock_market.StockSymbolUnrecognizedError`.

        The quantity `shares` to sell must be positive, yet less than or equal
        to this account's currently owned quantity. If `shares` is zero or
        less, this raises `StockShareQuantityError`. If `shares` is positive
        but greater than the quantity of `stock_symbol` owned, this
        method raises `InsufficientStockSharesError`. If this account cannot
        afford to pay the trading fee, `InsufficientBalanceError` is raised.

        Triggers `TRADER_ACCOUNT_SOLD` and `TRADER_ACCOUNT_UPDATED` if
        successful.
        """
        if self.is_frozen():
            raise FrozenError()

        if shares <= 0:
            raise StockShareQuantityError(stock_symbol, shares)
        elif shares > self._stocks[stock_sybol]:
            raise InsufficientStockSharesError(
                stock_symbol, shares, self._stocks[stock_sybol])

        price_per_share = self._market.get_stock_symbol_price(stock_symbol)
        profit = shares * price_per_share - self._trader.get_trading_fee()
        if self.get_balance() + profit < 0:
            # Trading fee made profit negative
            raise InsufficientBalanceError(
                stock_symbol, -profit, self.get_balance())

        # Make transaction
        self._balance += profit
        self._stocks[stock_symbol] -= shares
        #TODO: Broadcast TRADER_ACCOUNT_SOLD
        #TODO: Broadcast TRADER_ACCOUNT_UPDATED


    def get_statistics_daily(self
    ) -> typing.Dict[str, typing.Any]:
        """Return a `dict` of the current day's statistics collected during a
        simulation. Its keys identify trading statistics using
        display-language-independent English identifiers, like `'PROFIT_NET'`,
        and the associated values can be converted to `str`.

        This result may change upon `TRADER_ACCOUNT_UPDATED` events.
        """
        #TODO
        return {}

    def get_statistics_overall(self
    ) -> typing.Dict[str, typing.Any]:
        """Return a `dict` of overall running statistics collected during a
        simulation. Its keys identify trading statistics using
        display-language-independent English identifiers, like `'PROFIT_NET'`,
        and the associated values can be converted to `str`.

        This result may change upon `TRADER_ACCOUNT_UPDATED` events.
        """
        #TODO
        return {
            'PROFIT_NET': self._balance - self._balance_initial}




# Imported last to avoid circular dependencies
from model.stock_market import StockMarket
from model.trader import Trader