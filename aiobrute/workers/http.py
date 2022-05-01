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


from aiobrute.utils import show_error, show_info, show_success, WorkerException
from jinja2 import Environment, FileSystemLoader, select_autoescape
from requests.exceptions import ConnectionError, ReadTimeout
from jinja2.exceptions import TemplateNotFound
from aiobrute.configs import logger, version
from aiobrute.parser import templates_path
from aiobrute.worker import Worker
from bs4 import BeautifulSoup
import requests
import asyncio
import aiohttp

jinja = Environment(loader=FileSystemLoader(
    templates_path), autoescape=select_autoescape())

HTTP_SERVER_ERRORS = range(500, 512)
HTTP_CLIENT_ERRORS = range(400, 452)

class HTTPWorker(Worker):
    """
    HTTP worker for testing several http authentication mechanism
    """

    def __init__(self, options, *args):
        super().__init__(options, *args)
        self.resp_type = 'code' if 'code' in options.status_type else 'body'
        self.cookies = options.cookies or {}
        self.headers = options.headers or {}
        self.method = options.method.lower()
        self.use_template = options.template
        self.http_session = None
        self.template = None

        if options.fields:
            self.csrf_protect = bool('CSRF' in options.fields.keys())
        else:
            self.csrf_protect = None

        self.evaluation = {
            "^code": {
                "validator": f"return code != ({self.opt.status})",
                "condition": lambda a, b: a != b,
            },
            "code": {
                "validator": f"return code = ({self.opt.status})",
                "condition": lambda a, b: a == b
            },
            "^string": {
                "validator": f"string '{self.opt.status}' is not found in the response",
                "condition": lambda a, b: a not in b,
            },
            "string": {
                "validator": f"string '{self.opt.status}' is found in the response",
                "condition": lambda a, b: a in b
            }
        }

        self.condition = self.evaluation[self.opt.status_type]['condition']
        self.validator = self.evaluation[self.opt.status_type]['validator']

    def run(self):
        super().run()
        asyncio.run(self.http_session.close())

    async def handle_workers(self):
        self.headers.setdefault('User-Agent', f'aiobrute/{version}')

        if self.http_session is not None:
            await self.http_session.close()

        self.http_session = aiohttp.ClientSession(
            cookies=self.cookies, headers=self.headers)

        return await super().handle_workers()

    def prerun_hook(self):
        """ Initial tasks before starting the workers """

        if self.csrf_protect:
            print(show_info(
                f"Attempting to get initial CSRF cookies from '{self.opt.target}'..."))
            try:
                response = requests.get(self.opt.target, timeout=5)
                for cookie, value in response.cookies.get_dict().items():
                    self.cookies.setdefault(cookie, value)
                print(show_success(
                    "Cookies will be added to the subsequents requests"))
            except (ConnectionError, ReadTimeout):
                print(show_error(
                    f"The connection to '{self.opt.target}' has failed"))
                return False

        if self.use_template:
            protocol = self.opt.protocol.replace('_', '-')
            print(show_info(f"Loading template for '{protocol}' protocol"))
            try:
                self.template = jinja.get_template(f"{protocol}.jinja2")
            except TemplateNotFound:
                print(show_error(
                    f"Not able to get template for '{protocol}' protocol"))
                return False

        return True

    async def worker_prerun_hook(self):
        """ Attempt to get the initial CSRF token for the current worker """

        self.task.csrf_token = None

        if self.csrf_protect:
            logger.debug(f"Attempting getting initial CSRF token from '{self.opt.target}'", **self.context)

            async with self.http_session.get(self.opt.target, timeout=self.opt.timeout) as resp:
                self.get_csrf_token(await resp.text())

    async def request(self, method, resp_type, *args, **kwargs):
        """ Send request with the specified methods and options """

        async with self.http_session.request(method, self.opt.target, timeout=self.opt.timeout, *args, **kwargs) as resp:
            logger.info(self.get_protocol_message(
                self.task.password, method=f"[{self.opt.method}]", status=f"[{resp.status}]"), **self.context)

            body = await resp.text()
            status = str(resp.status) if resp_type == 'code' else body

            if 'server' in self.opt.http_error and resp.status in HTTP_SERVER_ERRORS:
                resp.raise_for_status()

            if 'client' in self.opt.http_error and resp.status in HTTP_CLIENT_ERRORS:
                resp.raise_for_status()

            if self.csrf_protect and not self.condition(self.opt.status, status):
                self.get_csrf_token(body)

            return status

    async def http_form_protocol_handler(self, password):
        """ Send encoded HTTP form requests """

        fields = self.get_fields(self.opt.username, password)
        params = { "data": fields } if self.opt.method == "POST" else { "params": fields }
        return await self.request(self.method, self.resp_type, allow_redirects=False, **params)

    async def basic_auth_protocol_handler(self, password):
        """ Send HTTP basic auth requests """

        return await self.request(self.method, self.resp_type, auth=aiohttp.BasicAuth(self.opt.username, password))

    async def wp_xmlrpc_protocol_handler(self, password):
        """ Send wordpress xmlrpc requests """

        payload = self.template.render({'username': self.opt.username, 'password': password})
        return await self.request(self.method, self.resp_type, data=payload)

    def get_exception_message(self, exception):
        """ Ensure that proper message is returned to the client on errors """

        message = super().get_exception_message(exception)

        try:
            raise(exception)
        except aiohttp.ClientPayloadError:
            message = "The server returned a malformed HTTP payload"
        except aiohttp.ClientConnectionError as err:
            message = err.__str__()
        except aiohttp.ClientResponseError as err:
            message = err.__str__()
        except asyncio.TimeoutError:
            message = f"Maximum wait time reached for the request ({self.opt.timeout})"
        except Exception:
            return message

        return message

    def get_csrf_token(self, response):
        """ Get the CSRF token from the request response body """

        soup = BeautifulSoup(response, features="html.parser")
        input_tag = soup.find('input', {'name': self.opt.fields["CSRF"]})

        csrf_token = input_tag['value'] if input_tag else None

        if csrf_token:
            logger.debug(f"CSRF token found '{csrf_token}'", **self.context)
            self.task.csrf_token = csrf_token
        else:
            raise WorkerException(
                "Not able to recover CSRF token from the response", "", self.task.name)

    def get_fields(self, username, password):
        """ Populate the corresponding auth fields with the appropriate identifier """

        fields = {}
        fields[self.opt.fields["USER"]] = username
        fields[self.opt.fields["PASS"]] = password

        if self.csrf_protect:
            fields[self.opt.fields['CSRF']] = self.task.csrf_token

        return {**self.opt.extra_fields, **fields} if self.opt.extra_fields else fields
