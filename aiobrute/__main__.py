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

from aiobrute.configs import logger, log_level_mapping
from aiobrute.utils import CustomFormatter, show_banner
from aiobrute.parser import options
from importlib import import_module
import logging
import sys

logger.level = getattr(logging, log_level_mapping[options.verbosity])
logger.handlers[0].setFormatter(CustomFormatter())

if sys.version_info < (3, 7):
    print("aiobrute requires python 3.7 or higher\n")
    sys.exit(1)

def run():
    module = import_module(f'aiobrute.workers.{options.worker}')
    worker = getattr(module, options.worker.upper() + 'Worker')

    show_banner()
    worker(options).run()

if __name__ == "__main__":
    run()