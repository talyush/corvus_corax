import socket
import time

name = "scan"

# ======================
# PORT CHECK
# ======================

def scan_port(ip, port, timeout=1):
    s = socket.socket()
    s.settimeout(timeout)

    try:
        s.connect((ip, port))
        return True
    except:
        return False
    finally:
        s.close()


# ======================
# SERVICE DETECT
# ======================

COMMON_PORTS = {
    21:"FTP",
    22:"SSH",
    23:"TELNET",
    25:"SMTP",
    53:"DNS",
    80:"HTTP",
    110:"POP3",
    143:"IMAP",
    443:"HTTPS",
    3306:"MySQL",
    3389:"RDP"
}

def detect_service(port):
    return COMMON_PORTS.get(port,"Unknown")


# ======================
# BANNER GRAB
# ======================

def banner_grab(ip, port):
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((ip, port))

        s.send(b"HEAD / HTTP/1.0\r\n\r\n")
        banner = s.recv(1024).decode(errors="ignore")

        print(f"[BANNER {port}] {banner.strip()}\n")
        s.close()

    except:
        print(f"[BANNER {port}] alınamadı")


# ======================
# SCAN MODES
# ======================

def normal_scan(ip,start,end):
    print("Normal scan başlatıldı\n")

    for port in range(start,end+1):
        if scan_port(ip,port):
            print(f"[OPEN] {port} ({detect_service(port)})")


def slow_scan(ip,start,end):
    print("Slow scan başlatıldı\n")

    for port in range(start,end+1):
        if scan_port(ip,port):
            print(f"[OPEN] {port} ({detect_service(port)})")
        time.sleep(0.3)


def banner_mode(ip,port):
    print("Banner grabbing...\n")

    if scan_port(ip,port):
        banner_grab(ip,port)
    else:
        print("Port kapalı.")


# ======================
# SUBNET SCAN
# ======================

def subnet_scan(base_ip):
    print("Subnet scan başlatıldı...\n")

    base = ".".join(base_ip.split(".")[:-1])

    for i in range(1,255):
        ip = f"{base}.{i}"

        if scan_port(ip,80,0.3) or scan_port(ip,22,0.3):
            print(f"[AKTİF] {ip}")


# ======================
# COMMAND HANDLER
# ======================

def run(args):

    if len(args) < 2:
        print("Kullanım:")
        print("scan <ip> normal <start> <end>")
        print("scan <ip> slow <start> <end>")
        print("scan <ip> banner <port>")
        print("scan <ip> subnet")
        return


    ip = args[0]
    mode = args[1]

    if mode == "normal":
        start = int(args[2])
        end = int(args[3])
        normal_scan(ip,start,end)

    elif mode == "slow":
        start = int(args[2])
        end = int(args[3])
        slow_scan(ip,start,end)

    elif mode == "banner":
        port = int(args[2])
        banner_mode(ip,port)

    elif mode == "subnet":
        subnet_scan(ip)

    else:
        print("Unknown mode.")