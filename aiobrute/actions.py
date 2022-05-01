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


from argparse import RawTextHelpFormatter, Action
import validators
import os
import re

class CustomFormatter(RawTextHelpFormatter):
    """ Custom formatter for clearer output in the help menu """

    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []
            if action.nargs == 0:
                parts.extend(action.option_strings)

            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                for option_string in reversed(action.option_strings):
                    if '--' in option_string:
                        parts.append('%s=%s' % (option_string, args_string))
                    else:
                        parts.append(option_string)

            return ', '.join(parts)

def configurable_action(CustomAction, **options):
    """ Class factory for generating configurable actions """

    class Custom(CustomAction):
        def __init__(self, *args, **kwargs):
            self.custom_options = options
            super().__init__(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            self.__populate_options()
            return super().__call__(*args, **kwargs)

        def __populate_options(self):
            for option, value in options.items():
                setattr(self, option, value)

    return Custom

class SeparatorAction(Action):
    def __call__(self, parser, namespace, value, *args):
        mistmatchs = [option for option in value if not re.fullmatch(
            fr"([-\w\d]*){self.separator}([-\w\d]*)", option)]

        if not mistmatchs:
            value = dict([tuple(data.split(self.separator)) for data in value])
            if 'schema' in self.custom_options and not self.schema.is_valid(value):
                parser.error(
                    f"The {self.option_strings[0]} option is missing one of the following mandatory field: [{', '.join(self.schema.schema.keys())}]")
            else:
                setattr(namespace, self.dest, value)
        else:
            parser.error(
                f"The {self.option_strings[0]} option is not using a valid format. Please use the following format: \"key{self.separator}value ...\"")

class StatusTypeAction(Action):
    def __call__(self, parser, namespace, value, *args):
        option = self.option_strings[0].strip("--")

        if option == 'string':
            status_type = '^string' if value.startswith('^') else 'string'
        else:
            status_type = '^code' if value.startswith('^') else 'code'

        setattr(namespace, 'status_type', status_type)
        setattr(namespace, self.dest, value.strip('^'))

class WorkerAction(Action):
    def __call__(self, parser, namespace, value, *args):
        if value < 1 or value > 100:
            parser.error(
                "The number of workers must be lower than 100 and higher than 1")
        else:
            setattr(namespace, self.dest, value)

class PathAction(Action):
    def __call__(self, parser, namespace, value, *args):
        if os.path.exists(value):
            setattr(namespace, self.dest, value)
        else:
            parser.error(f"'{value}' do not exist or is not a valid file path")

class URLAction(Action):
    def __call__(self, parser, namespace, value, *args):
        if validators.url(value):
            setattr(namespace, self.dest, value)
        else:
            parser.error(f"'{value}' is not a valid HTTP url")

class RequestTypeAction(Action):
    def __call__(self, parser, namespace, value, *args):
        if value in ['wp-xmlrpc']:
            setattr(namespace, 'template', True)
        else:
            setattr(namespace, 'template', False)

        setattr(namespace, self.dest, value.replace("-", "_"))
