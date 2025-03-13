# SandwichBot
The original purpose of this project was to show how sandwich attacks work and to promote Python language in Web3, but any hebaviour detrimental to others' interests is not advocated, and please pay attention to your own safety!

⚠️ The project is still under development.

## How to run

Finish the Prerequisites first

### Configuration
copy `.env.example` to `.env` and fill in the required information
.env
```shell
infura_api_key = your_infura_api_key_here
```
modify the `config.py` file if necessary

### Account
Generate a keystroke file
```shell
python account.py
```
⚠️You have to remember your password. If your private key is not saved elsewhere, forgetting your password is equivalent to losing your account.

### Run the bot
```shell
python main.py
```

## Prerequisites

- Python 3.11 or higher
- Install the required packages
```shell
pip install -r requirements.txt
```
- Register an account on [Infura](https://infura.io/) and get an API key