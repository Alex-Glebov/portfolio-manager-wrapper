# Portfolio Manager Wrapper

Python wrapper for Portfolio Manager API with both synchronous and asynchronous support.

## Features

- **Sync & Async**: Both `PortfolioManager_API` and `PortfolioManager_API_Async` classes
- **Auto Authentication**: Automatic login and token refresh
- **Context Managers**: Proper resource management with `with` and `async with`
- **Portfolio Support**: Multi-portfolio API with default portfolio setting
- **Error Handling**: Comprehensive exception hierarchy
- **Configurable**: Args > Environment variables > Config file > Defaults

## Installation

```bash
pip install portfolio-manager-wrapper
```

## Quick Start

### Synchronous

```python
from portfolio_manager_wrapper import PortfolioManager_API

# Using context manager (recommended)
with PortfolioManager_API() as api:
    # Get all transactions
    transactions = api.get_transactions(limit=10)
    
    # Create a transaction
    result = api.create_transaction(
        name="Bitcoin",
        cost=50000.00,
        qty=0.5,
        cost_units="USD",
        direction="in",
        counterpart_id="exchange_a"
    )
    
    # Get holdings
    holdings = api.get_holdings()
    print(holdings)
```

### Asynchronous

```python
import asyncio
from portfolio_manager_wrapper import PortfolioManager_API_Async

async def main():
    async with PortfolioManager_API_Async() as api:
        transactions = await api.get_transactions(limit=10)
        print(transactions)

asyncio.run(main())
```

## Configuration

Priority (highest to lowest):
1. Constructor arguments
2. Environment variables
3. Config file (`PortfolioManager_API_Config.ini`)
4. Default values

### Environment Variables

```bash
export PORTFOLIO_MANAGER_HOST=localhost
export PORTFOLIO_MANAGER_PORT=8000
export PORTFOLIO_MANAGER_USER=admin
export PORTFOLIO_MANAGER_PASSWORD=your_password
```

### Config File

See `PortfolioManager_API_Config.ini.example` for template.

### Constructor Arguments

```python
api = PortfolioManager_API(
    host="localhost",
    port=8000,
    username="admin",
    password="your_password",
    timeout=30,
    portfolio="default"  # Default portfolio for all requests
)
```

## API Methods

### Transactions

- `create_transaction(name, cost, qty, cost_units, direction, counterpart_id, notes=None, portfolio=None)`
- `get_transactions(name=None, direction=None, counterpart_id=None, limit=100, offset=0, portfolio=None)`
- `get_transaction(transaction_id, portfolio=None)`
- `update_transaction(transaction_id, updates, portfolio=None)`
- `delete_transaction(transaction_id, portfolio=None)`

### Holdings

- `get_holdings(name=None, portfolio=None)`
- `get_holding(item_name, portfolio=None)`
- `get_portfolio_summary(portfolio=None)`
- `get_counterpart_history(counterpart_id, portfolio=None)`

### Exports

- `export_transactions(save_path=None, portfolio=None)` - Returns CSV bytes
- `export_holdings(save_path=None, portfolio=None)` - Returns CSV bytes

### System

- `get_version()` - Get API version info
- `health_check()` - Check API health

## Portfolio Support

The wrapper supports Portfolio Manager's multi-portfolio feature:

```python
# Set default portfolio for the instance
api = PortfolioManager_API(portfolio="my_portfolio")

# Or override per-request
api.get_transactions(portfolio="other_portfolio")

# Empty string "" means default portfolio (accessible by all users)
api.get_transactions(portfolio="")
```

## Error Handling

```python
from portfolio_manager_wrapper import (
    PortfolioManagerError,
    AuthenticationError,
    ConnectionError,
    APIError,
    ValidationError
)

try:
    with PortfolioManager_API() as api:
        api.create_transaction(...)
except AuthenticationError as e:
    print(f"Login failed: {e}")
except ConnectionError as e:
    print(f"Cannot connect: {e}")
except APIError as e:
    print(f"API error {e.status_code}: {e.response}")
except ValidationError as e:
    print(f"Invalid data: {e}")
```

## Requirements

- Python 3.8+
- httpx 0.24+

## License

MIT
