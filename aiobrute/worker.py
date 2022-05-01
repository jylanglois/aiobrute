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


from aiobrute.utils import (
    equal,
    color,
    show_info,
    show_result,
    show_error,
    show_success,
    show_context,
    validate_choice,
    ValidPassword,
    WorkerException
)
from aiobrute.parser import wordlists_path
from aiobrute.configs import logger
from alive_progress import alive_bar
import asyncio
import logging
import sys
import os

class Worker():
    """Base worker class

       This class generates and handles the worker's lifecycle. Each worker is an
       asyncio task that consumes a queue that has been feeded by the selected
       wordlist.

       Creating a new worker can be done by subclassing this class and creating a method
       starting with the protocol name and ending with _protocol_handler. That method is
       called for each entry in the queue and must return a status that indicates if the
       candidate is valid.

       ex: async ssh_protocol_handler()

       The prerun_hook() method can be used to run tasks before the workers are started.
       The worker_prerun_hook() and worker_postrun_hook() methods can also be used for
       running tasks during the lifecycle of the workers.

    """

    validator = "login successful"

    def __init__(self, options):
        self.opt = options
        self.condition = equal
        self.request_handler = self.get_protocol_handler()
        self.trace = bool(self.opt.verbosity > 2)
        self.queue = asyncio.Queue()
        self.initial_qsize = 0
        self.remaining_tasks = []
        self.worker_count = 0
        self.retry_count = 0
        self.worker_errors = []

    def run(self):
        unpaused = True

        if self.opt.wordlist_file is None:
            wordlist_file = os.path.join(wordlists_path, self.opt.wordlist + ".txt")
            print(show_info(f"Loading data from the '{self.opt.wordlist}' built-in wordlist"))
        else:
            wordlist_file = self.opt.wordlist_file
            print(show_info(f"Loading data from the '{wordlist_file}' wordlist file"))

        with open(wordlist_file, 'r') as wordlist:

            if not self.prerun_hook():
                sys.exit(show_error(
                    "Some prerun tasks has failed to run, canceling the execution of the bruteforce..."))

            for word in wordlist.read().splitlines():
                self.queue.put_nowait(word)

            self.initial_qsize = self.queue.qsize()

            print("\n" + show_context(capitalize=True, worker_type=self.opt.worker,
                  target=self.opt.target, workers=self.opt.workers, wordlist_size=self.queue.qsize(), ) + "\n")

            while unpaused:
                try:
                    valids, errors = asyncio.run(self.handle_workers())
                    if valids:
                        print("\n" + show_success(f"{len(valids)} possible valid candidates found\n"))
                        values = [list((self.validator, self.opt.username, password)) for password in valids]
                        show_result(values, ('Reason', 'Username', 'Password'), colored=color.GREEN)

                    elif not self.queue.empty():
                        print("\n" + show_error(f"Error threshold breached ({self.opt.max_retries}), showing last error from some workers..." + "\n"))
                        values = [list((error.worker, error.password,  error)) for error in errors[:5]]
                        show_result(values, ('Worker', 'Last Password', 'Last Error'), colored=color.RED)
                    else:
                        print("\n" + show_info("No password have been found"))
                    unpaused = False
                except KeyboardInterrupt:
                    try:
                        unpaused = validate_choice(
                            "\n" + "The execution of the bruteforce has been paused. Do you want to continue? (Y/N)")
                    except KeyboardInterrupt:
                        return

                finally:
                    self.worker_count = 0

    async def handle_workers(self):
        """ Start and handle the worker's lifecycle """

        event, tasks = asyncio.Event(), []
        tasks.extend([asyncio.create_task(self.rerun_on_exception(
            self.worker, event)) for __ in range(self.opt.workers)])

        if logging.getLevelName(logger.level) == "CRITICAL":
            tasks.append(asyncio.create_task(self.stats_worker(event)))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        valids = [result for result in results if isinstance(result, ValidPassword)]
        errors = [result for result in results if isinstance(result, WorkerException)]

        return valids, errors

    async def worker(self, event):
        """ The worker that will make the request and process the queue """

        status, unstarted = '', True

        while not any([self.condition(self.opt.status, status), self.queue.empty()]) or unstarted:
            unstarted = False
            if event.is_set():
                raise asyncio.CancelledError()

            password = await self.queue.get()
            self.task.position = self.initial_qsize - self.queue.qsize()
            self.task.password = password

            status = await self.request_handler(password)

        if self.condition(self.opt.status, status):
            logger.debug("Password possibly found, sending event to other workers...", **self.context); event.set()
            return ValidPassword(password=password, status=status, reason=self.validator)

    async def rerun_on_exception(self, coro, event, *args):
        """ Wrapper function that rerun the worker if an exception happen """

        self.set_task_name()

        while self.retry_count <= self.opt.max_retries:
            try:
                await self.worker_prerun_hook()
                password = await coro(event, *args)
            except Exception as err:
                if isinstance(err, asyncio.CancelledError):
                    logger.debug("Stopping current worker", **self.context)
                    await self.queue.put(self.task.password)
                    await self.worker_postrun_hook()
                    raise asyncio.CancelledError from err
                else:
                    self.retry_count += 1
                    logger.error("%s", err, exc_info=self.trace, **self.context)
                    logger.debug("Attempt failed for candidate '%s'. The password is being sent back in the queue", self.task.password, **self.context)
                    await self.queue.put(self.task.password)
                    last_error = WorkerException(self.get_exception_message(
                        err), self.task.password, self.task.name)
            else:
                return password

        if not self.queue.empty():
            logger.debug("Error threshold breached, stopping current worker", **self.context); event.set()
        else:
            logger.debug("The queue is empty, stopping current worker", **self.context)

        await self.worker_postrun_hook()

        return last_error

    async def stats_worker(self, event):
        """ Show the progress based on the remaining items in the queue """

        def get_progress():
            while not self.queue.empty():
                yield self.initial_qsize - self.queue.qsize()
            yield self.initial_qsize - self.queue.qsize()

        with alive_bar(self.initial_qsize, manual=True) as bar:
            for size in get_progress():
                if event.is_set():
                    return None
                else:
                    await asyncio.sleep(0.0001)
                    bar(size / self.initial_qsize)

    def get_protocol_handler(self):
        """ Return the appropriate request handler based on the login type option """

        try:
            return getattr(self, f"{self.opt.protocol}_protocol_handler")
        except AttributeError:
            raise AttributeError(
                f"No request handler function found for {self.opt.protocol}") from AttributeError

    def get_protocol_message(self, password, **kwargs):
        debug_message = show_context(**kwargs, separator='-', target=self.opt.target, username=self.opt.username, password=password)
        debug_message += f" - ({self.task.position} of {self.initial_qsize})"
        return debug_message

    def get_exception_message(self, exception):
        """ Use this method for showing expected error messages coming from the workers """
        message = exception.__str__()
        return message if message else "Unknown Error"

    def set_task_name(self):
        self.worker_count += 1
        self.task.name = f"worker {self.worker_count}"

    def prerun_hook(self):
        """ Use this method to perform pretask before running the workers """
        return True

    async def worker_prerun_hook(self):
        """ Use this method to perform task asynchronously before each worker start or restart """

    async def worker_postrun_hook(self):
        """ Use this method to perform task asynchronously when the worker is stopped or cancelled """

    @property
    def task(self):
        return asyncio.current_task()

    @property
    def context(self):
        return {"extra": {"worker_type": self.opt.worker.upper(), "task_name": self.task.name}}
