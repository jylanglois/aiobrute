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
import asyncio
import aiomysql
import pymysql

class MYSQLWorker(Worker):
    """
    MYSQL worker for testing mysql authentication mechanism
    """

    async def mysql_protocol_handler(self, password):
        """ perform mysql connections attempts """

        try:
            logger.info(self.get_protocol_message(password), **self.context)
            await aiomysql.connect(host=self.opt.target, port=self.opt.port, user=self.opt.username, password=password)
        except pymysql.err.Error as err:
            original = err.__context__
            if original.args and original.args[0] == 1045:
                return False
            elif isinstance(original, asyncio.CancelledError):
                raise original
            else:
                raise
        else:
            return True