import os

import vk_parser as vk_parser

def run_module(name, func):
    try:
        # console.print(f"[yellow]↪ Running{name}... (Press Ctrl+C to cancel)[/yellow]")
        # if use_proxy:
        #    func(proxy=get_proxy())
        # else:
            func()
    except KeyboardInterrupt:
        print(f"\n[red]❌ {name} canceled by user.[/red]")
    except Exception as e:
        print(f"[red]✘ Error in module {name}: {e}")
    

def main():
    os.makedirs("logs", exist_ok=True)
    while True:
        try:
            
            choice = input("Введи цифру:")

            if choice == "0":
                run_module("Find VK", vk_parser.run)
            elif choice == "9":
                print("not yet")
                # run_module("Telegram OSINT Scraper", telegram_scraper.run)
            elif choice == "99":
                print("[bold red]Exit CryptDefender. See you![/bold red]")
                break
            else:
                print("[yellow]✘ Invalid input. Select a number from 0 to 9.[/yellow]")
                

        except KeyboardInterrupt:
            continue 

main()