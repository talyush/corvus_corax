import core.loader
print("LOADER PATH:",core.loader.__file__)

from core.loader import load_modules
from core.banner import show_banner

modules = load_modules()
print("loaded modules:", modules.keys())

show_banner()

def main():
    while True:
        cmd = input("corvus > ").strip().split()

        if not cmd:
            continue

        command = cmd[0]

        if command == "exit":
            break

        elif command in modules:
            modules[command].run(cmd[1:])

        else:
            print("Unknown command. Type 'help'.")
if __name__ == "__main__":
    main()