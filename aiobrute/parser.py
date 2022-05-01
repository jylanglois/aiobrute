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


from aiobrute.actions import (
    CustomFormatter,
    WorkerAction,
    PathAction,
    URLAction,
    SeparatorAction,
    RequestTypeAction,
    StatusTypeAction,
    configurable_action,
)
from aiobrute.configs import version
from schema import Schema
import argparse
import sys
import os

examples = """
Examples:
  %(prog)s http --help  # show options for the http module
"""

parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wordlists_path = os.path.join(parent, os.path.normpath('resources/wordlists'))
templates_path = os.path.join(parent, os.path.normpath('resources/templates'))

wordlists = [os.path.splitext(wordlist)[0] for wordlist in os.listdir(wordlists_path)]

custom_formater = lambda prog: CustomFormatter(prog, max_help_position=45, width=140)


parser = argparse.ArgumentParser(
    prog='aiobrute', usage="%(prog)s [MODULE] [OPTIONS]", description=examples, formatter_class=custom_formater)

subparsers = parser.add_subparsers(
    title='available modules', dest='worker', metavar='modules', help='description')

parser.add_argument(
    "--version",
    action='version',
    version=f'%(prog)s {version}'
)

def general_settings(subparser):
    """ Common options for all workers subparsers """

    common_group = subparser.add_argument_group("General Settings")
    wordlist_group = common_group.add_mutually_exclusive_group()

    common_group.add_argument(
        '--verbosity', '-v',
        help="specify if you want want the debug output",
        action="count",
        default=0
    )
    common_group.add_argument(
        "--workers", '-w',
        help="number of worker for processing the requests (default: %(default)s)",
        type=int,
        default=15,
        action=WorkerAction,
        metavar="NUM"
    )
    common_group.add_argument(
        '--max-retries', '-r',
        help="maximum number of retries before interrupting the bruteforce (default: %(default)s)",
        type=int,
        default=50,
        metavar="NUM"
    )
    common_group.add_argument(
        '--username', '-u',
        help="username that will be used for the bruteforce",
        required=True,
        metavar="USER"
    )
    wordlist_group.add_argument(
        '--wordlist', '-l',
        help="the built-in that will be used for the bruteforce",
        default="rockyou",
        choices=wordlists,
        metavar="LIST"
    )
    wordlist_group.add_argument(
        '--wordlist-file', '-L',
        help="the wordlist file that will be used for the bruteforce",
        action=PathAction,
        metavar='PATH'
    )

    return subparser

# Parser for HTTP worker options

http_examples = """
Examples:
  aiobrute http -t http://localhost -u admin -m GET -p basic-auth -c ^401
  aiobrute http -t http://localhost/wp-login.php -u admin -m POST -p http-form -c 302 -f USER:log PASS:pwd
  aiobrute http -t http://localhost/xmlrpc.php -u admin -m POST -p wp-xmlrpc -s '^faultCode'
"""

http_parser = general_settings(subparsers.add_parser(
    "http", usage='aiobrute http [OPTIONS]', help="module for testing http authentication mechanism", description=http_examples, formatter_class=custom_formater))

http_group = http_parser.add_argument_group("HTTP Settings")
http_group.set_defaults(status_type="code")

status_group = http_group.add_mutually_exclusive_group()

schema = Schema({'USER': str, 'PASS': str}, ignore_extra_keys=True)

allowed_method = {
    "http_form": ('POST', 'GET', 'HEAD'),
    "basic_auth": ('GET', 'HEAD'),
    "wp_xmlrpc": ('POST')
}

http_group.add_argument(
    "--target", "-t",
    help='the URL that will be used for brute forcing the password',
    action=URLAction,
    required=True,
    metavar='URL'
)
http_group.add_argument(
    "--fields", "-f",
    help="the form fields to use (\"<USER>:userfield <PASS>:passfield <CSRF>:csrfield\")",
    required=False,
    nargs='+',
    action=configurable_action(SeparatorAction, separator=":", schema=schema)
)
http_group.add_argument(
    "--extra-fields", "-e",
    help="additional form fields (\"field:value\")",
    required=False,
    nargs='+',
    action=configurable_action(SeparatorAction, separator=":"),
    metavar='FIELDS'
)
http_group.add_argument(
    "--headers", "-H",
    help="headers to add or override in the request (\"header:value\")",
    nargs='+',
    action=configurable_action(SeparatorAction, separator=":")
)
http_group.add_argument(
    "--cookies", "-C",
    help="cookies to add or override in the request (\"cookie=value\")",
    nargs='+',
    action=configurable_action(SeparatorAction, separator="=")
)
http_group.add_argument(
    "--protocol", "-p",
    help="the authentication protocol to use (default: http-form)",
    choices=['http-form', 'basic-auth', 'wp-xmlrpc'],
    action=RequestTypeAction,
    required=True,
    metavar='PROTOCOL'
)
http_group.add_argument(
    "--method", "-m",
    help="the http method used when making the requests",
    choices=['POST', 'GET', 'HEAD'],
    required=True,
    metavar='METHOD'
)
http_group.add_argument(
    "--timeout", "-T",
    help="number of seconds that a worker should wait before returning an error",
    type=int,
    default=15,
    metavar='NUM'
)
http_group.add_argument(
    "--http-error", "-E",
    help="type of http errors that invalidate the password (server, client, noerror)",
    nargs='+',
    choices=['server', 'client', 'noerror'],
    default='server',
    metavar='TYPE'
)
status_group.add_argument(
    "--string", "-s",
    dest="status",
    help="validate password with the returned string ('^' prefix for inverse match)",
    action=StatusTypeAction,
    metavar='STRING'
)
status_group.add_argument(
    "--code", "-c",
    help="validate password with the returned code ('^' prefix for inverse match)",
    dest="status",
    action=StatusTypeAction,
    metavar='CODE'
)

# Parser for SSH worker options

ssh_examples = """
Examples:
  aiobrute ssh -u admin -t localhost
"""

ssh_parser = general_settings(subparsers.add_parser(
    "ssh", usage='aiobrute ssh [OPTIONS]', help="module for testing ssh authentication mechanism", description=ssh_examples, formatter_class=custom_formater))

ssh_group = ssh_parser.add_argument_group("SSH Settings")
ssh_group.set_defaults(status=True, protocol="ssh")

ssh_group.add_argument(
    '--target', '-t',
    help='the hostname or ip address of the ssh server',
    required=True,
    metavar='HOST'
)
ssh_group.add_argument(
    '--port', '-p',
    help="the port used by the ssh server (default: 22)",
    default=22,
    type=int,
    metavar='NUM'
)


# Parser for ftp worker options

ftp_examples = """
Examples:
  aiobrute.py ftp -u admin -t localhost
"""

ftp_parser = general_settings(subparsers.add_parser(
    "ftp", usage='aiobrute ftp [OPTIONS]', help="module for testing ftp authentication mechanism", description=ftp_examples, formatter_class=custom_formater))

ftp_group = ftp_parser.add_argument_group("FTP Settings")
ftp_group.set_defaults(status=True, protocol="ftp")

ftp_group.add_argument(
    '--target', '-t',
    help='the hostname or ip address of the ftp server',
    required=True
)

ftp_group.add_argument(
    '--port', '-p',
    help="the port used by the ftp server (default 21)",
    default=21,
    type=int
)


# Parser for mysql options

mysql_examples = """
Examples:
  aiobrute.py mysql -u admin -t localhost
"""

mysql_parser = general_settings(subparsers.add_parser(
    "mysql", usage='aiobrute mysql [OPTIONS]', help="module for testing mysql authentication mechanism", description=mysql_examples, formatter_class=custom_formater))

mysql_group = mysql_parser.add_argument_group("MYSQL Settings")
mysql_group.set_defaults(status=True, protocol="mysql")

mysql_group.add_argument(
    '--target', '-t',
    help='the hostname or ip address of the mysql server',
    required=True
)

mysql_group.add_argument(
    '--port', '-p',
    help="the port used by the mysql server (default 3306)",
    default=3306,
)

options = parser.parse_args()

if options.worker is None:
    parser.print_help()
    sys.exit(0)

if options.verbosity > 3:
    parser.error("Invalid verbosity level")

if options.worker == "HTTP":

    if options.method not in allowed_method[options.protocol] and options.method:
        http_parser.error(f"The '{options.method}' http method is not not allowed when using '{options.protocol}' protocol")

    if options.protocol == "http_form" and not options.fields:
        http_parser.error("The following arguments is required when using the 'http-from' protocol: --fields/f")

    if not options.status:
        http_parser.error("The following arguments are required: --code/-c or --string/-s")
