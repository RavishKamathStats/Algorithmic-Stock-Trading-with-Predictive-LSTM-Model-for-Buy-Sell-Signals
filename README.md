# DSCI 560 Lab 3 Part 2

## Analysing Time Series and ML models to Stock Portfolios


## Installation

In order to run all the files for the part 2. We first need to activate the specific environment to get the right packages and their version.

```bash
source stock_algo_env/bin/activate
pip install -r requirements.txt
```
## Deployment

To first access the data, you can look at the directory called Part_1_Edited to get your data into your specified database. You may need to create your own database called "stockTrading". And make sure you have all privileges availble for the user you created. 

```bash
  cd Part_1_Edited
  python3 run_stock_trading.py
```

Follow the prompts to design your own portfolio. In order to RUN the models, your data must exist in the database! You can also export to a csv file. Just follow the prompts.

To run all the models:

```bash
cd ..
```

From there you can run any of the files that start with "run" to test out the models on your specified portfolio. Just follow the prompts.

Example:

```bash
python3 run run_mock_trade.py

```
