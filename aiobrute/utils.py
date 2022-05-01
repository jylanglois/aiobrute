#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  Author: Jean-Yann Barsalou-Langlois

from prettytable import PrettyTable, HEADER
from dataclasses import dataclass
from aiobrute.configs import version
import logging

@dataclass
class ValidPassword():

    def __str__(self):
        return self.password

    password: str
    status: str
    reason: str


@dataclass
class Color():
    CYAN: str = "\033[96m"
    DARKCYAN: str = "\033[36m"
    GREEN: str = "\033[92m"
    BLUE: str = "\033[94m"
    YELLOW: str = "\033[93m"
    RED: str = "\033[91m"
    BOLD: str = "\033[1m"
    ENDC: str = "\033[0m"


color = Color()


class WorkerException(Exception):
    """General worker error

       Exception raised when the worker encounters an error. The password
       that was processed by the worker and the name of the worker are added
       as an attribute

    """

    def __init__(self, reason, password, worker):
        super().__init__(reason)
        self.password = password
        self.worker = worker


def get_format(
    level): return f"%(asctime)s - [%(worker_type)s] [{level}] - %(message)s - [%(task_name)s]"


class CustomFormatter(logging.Formatter):

    FORMATS = {
        logging.CRITICAL: f"{get_format(color.RED + 'CRITICAL' + color.ENDC)}",
        logging.ERROR: f"{get_format(color.RED + 'ERROR' + color.ENDC)}",
        logging.WARNING: f"{get_format(color.RED + 'WARNING' + color.ENDC)}",
        logging.INFO:  f"{get_format(color.CYAN + 'INFO' + color.ENDC)}",
        logging.DEBUG: f"{get_format(color.YELLOW + 'DEBUG' + color.ENDC)}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def show_success(text):
    return f"{color.GREEN}[+]{color.ENDC} {text}"


def show_info(text):
    return f"{color.CYAN}[-]{color.ENDC} {text}"


def show_entry(text):
    return f"{color.CYAN}[!]{color.ENDC} {text}"


def show_error(text):
    return f"{color.RED}[!]{color.ENDC} {text}"


def show_debug(text):
    return f"{color.YELLOW}[-]{color.ENDC} {text}"


def show_input(text):
    return f"{color.BOLD}{text}{color.ENDC}\n"


def show_context(capitalize=False, separator='|', **kwargs):
    """ Convert keywords arguments to a string with entries separated by the chosen separator """

    result = ""

    for key, value in kwargs.items():
        spaced = key.replace('_', ' ')
        key = " ".join([word.capitalize()
                       for word in spaced.split(" ")]) if capitalize else spaced
        result += f"{key}: {color.YELLOW}{value}{color.ENDC} {separator} "

    return result[:-3]

def show_result(values, fields, colored=None):
    """ Show result in a table and optionally add color to rows """

    pretty = PrettyTable(hrules=HEADER, junction_char='-',
                         right_padding_width=2, left_padding_width=1)

    pretty.field_names = fields
    pretty.align = "l"

    if colored is not None:
        for value in values:
            colored_values = list(
                map(lambda value: f"{colored}{value}{color.ENDC}", value))
            pretty.add_row(colored_values)
    else:
        pretty.add_rows(values)

    print(pretty)

def validate_choice(text):
    choice = input("\n" + show_input(text))

    while choice not in ['y', 'yes', 'n', 'no']:
        print("\n" + show_error("Please enter a valid input (yes/y/no/n/)"))
        choice = input(show_input(text))

    return True if choice in ['y', 'yes'] else False


def show_banner():
    print(f"""
    ░█████╗░██╗░█████╗░██████╗░██████╗░██╗░░░██╗████████╗███████╗
    ██╔══██╗██║██╔══██╗██╔══██╗██╔══██╗██║░░░██║╚══██╔══╝██╔════╝
    ███████║██║██║░░██║██████╦╝██████╔╝██║░░░██║░░░██║░░░█████╗░░
    ██╔══██║██║██║░░██║██╔══██╗██╔══██╗██║░░░██║░░░██║░░░██╔══╝░░
    ██║░░██║██║╚█████╔╝██████╦╝██║░░██║╚██████╔╝░░░██║░░░███████╗
    ╚═╝░░╚═╝╚═╝░╚════╝░╚═════╝░╚═╝░░╚═╝░╚═════╝░░░░╚═╝░░░╚══════╝

              https://github.com/jylanglois/aiobrute

                    version: [{version} - alpha]
    """)

def equal(a, b):
    return a == b
