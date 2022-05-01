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


from aiobrute.worker import Worker
from aiobrute.configs import logger
import aioftp


class FTPWorker(Worker):
    """
    FTP worker for testing ftp authentication mechanism
    """

    validator = "(230) login successful"

    async def worker_prerun_hook(self):
        self.task.client = aioftp.Client()

    async def worker_postrun_hook(self):
        logger.debug("Closing the ftp connection for the worker", **self.context)
        self.task.client.close()

    async def ftp_protocol_handler(self, password):
        """ perform ftp connection attempts """

        try:
            logger.info(self.get_protocol_message(password), **self.context)
            await self.task.client.connect(self.opt.target, self.opt.port)
            await self.task.client.login(self.opt.username, password)
        except aioftp.errors.StatusCodeError as err:
            self.task.client.close()
            if '530' in err.received_codes:
                return False
            else:
                raise err
        else:
            return True
