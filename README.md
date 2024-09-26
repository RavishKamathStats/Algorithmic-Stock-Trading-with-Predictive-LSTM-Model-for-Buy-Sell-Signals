# Algorithmic Stock Trading with Predictive LSTM Model for Buy/Sell Signals


## Installation

We first need to activate the specific environment to get the right packages and their version.

```bash
source .venv/bin/activate
```
## Deployment

First create your own user name and portfolio by following the portfolio maker directory. From there run the stock_trading script and follow the prompts. 

```bash
  cd portfolio_maker
  python3 run_stock_trading.py
```

Follow the prompts to design your own portfolio. In order to RUN the models, your data must exist in the database! You can also export to a csv file. Just follow the prompts.

To run all the models:

```bash
cd algorithmic_trading
```

From there you can run any of the files that start with "run" to test out the models on your specified portfolio. Just follow the prompts.

Example:

```bash
python3 run run_mock_trade.py

```
