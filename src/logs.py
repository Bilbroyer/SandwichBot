# logs.py

from colorama import init, Fore, Style
import sys
import datetime

# 初始化 colorama
init(autoreset=True)

def log_warn(*args):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] " + Fore.YELLOW + ' '.join(map(str, args)))

def log_success(*args):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] " + Fore.GREEN + ' '.join(map(str, args)))

def log_info(*args):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] " + Fore.CYAN + ' '.join(map(str, args)))

def log_error(*args):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] " + Fore.RED + ' '.join(map(str, args)), file=sys.stderr)

def log_trace(*args):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] " + Fore.WHITE + Style.DIM + ' '.join(map(str, args)))

def log_debug(*args):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] " + Fore.MAGENTA + ' '.join(map(str, args)))

def log_fatal(*args):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] " + Fore.RED + Style.BRIGHT + ' '.join(map(str, args)), file=sys.stderr)
