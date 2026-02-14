name = "help"

def run(args):
    print("""
Available Commands:

scan <ip>        → ping + port scan
help             → show commands
version          → show tool version
footprint <domain> → get IP and hostname
geoip <ip>       → get geolocation info
netscan <ip,network> → scan network
""")