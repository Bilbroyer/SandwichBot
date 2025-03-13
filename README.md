# SandwichBot
The original purpose of this project was to show how sandwich attacks work and to promote Python language in Web3, but any hebaviour detrimental to others' interests is not advocated, and please pay attention to your own safety!

The project is still under development.

## How to run

⚠️ if you don't have Python installed, jump at Prerequisites

### env
copy `.env.example` to `.env` and fill in the required information

.env
```shell
infura_api_key = your_infura_api_key_here
```

## Prerequisites

- Python 3.11 or higher
- Install the required packages
```shell
pip install -r requirements.txt
```
- Generate a keystroke file
```shell
python generate_keystroke.py
```
- Register an account on [Infura](https://infura.io/) and get an API key