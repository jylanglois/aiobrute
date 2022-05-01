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
import asyncssh


class SSHWorker(Worker):
    """
    SSH worker for testing ssh authentication mechanism
    """

    async def ssh_protocol_handler(self, password):
        """ perform SSH connections attempts """

        try:
            logger.info(self.get_protocol_message(password), **self.context)
            await asyncssh.create_connection(asyncssh.SSHClient, self.opt.target, port=self.opt.port, password=password, username=self.opt.username)
        except asyncssh.misc.PermissionDenied:
            return False
        else:
            return True