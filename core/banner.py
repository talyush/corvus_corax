name = "banner"
from colorama import Fore, Style, init

def show_banner():
    init(autoreset=True)

    title_art = r"""
 ____     _____   ____    __  __  __  __  ____       
/\  _`\  /\  __`\/\  _`\ /\ \/\ \/\ \/\ \/\  _`\     
\ \ \/\_\\ \ \/\ \ \ \L\ \ \ \ \ \ \ \ \ \ \,\L\_\   
 \ \ \/_/_\ \ \ \ \ \ ,  /\ \ \ \ \ \ \ \ \/_\__ \   
  \ \ \L\ \\ \ \_\ \ \ \\ \\ \ \_/ \ \ \_\ \/\ \L\ \ 
   \ \____/ \ \_____\ \_\ \_\ `\___/\ \_____\ `\____\
    \/___/   \/_____/\/_/\/ /`\/__/  \/_____/\/_____/
"""

    lower_art = r"""

        C O R V U S   C O R A X
      [ See The Unseen Engine ]

             \\
              \\_
           .--.
          |o_o |
          |:_/ |
         //   \ \
        (|     | )
       /'\_   _/`\
       \_)=(_/

        v0.4  |  Modular Recon Framework
    """
    print(Fore.MAGENTA + title_art + Style.RESET_ALL + lower_art)