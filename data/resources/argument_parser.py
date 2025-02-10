import sys

from rich import get_console
from os_flags import *

console = get_console()


class Argument:
    def __init__(self, name, args, triggers, description, positional=False):
        self.name = name
        self.nargs = len(args)
        self.args = args
        self.triggers = triggers
        self.positional = positional

        self._description = description

    def description(self):
        if self.nargs < 2:
            return f'{self.name} | {self._description}'
        return f'{self.name} => {" ".join(self.args)} | {self._description}'

    def short(self):
        if self.nargs < 2:
            return f'[{self.name}]'
        else:
            return f'[{self.name} {" ".join(self.args)}]'

    def __call__(self, args):
        self.triggers(*args)


class Flag:
    def __init__(self, name, mini, value, triggers, description, allow_end=False):
        self.name = name
        self.mini = mini
        self.value = value
        self.triggers = triggers

        self._description = description
        self.allow_end = allow_end

    def description(self):
        if self.value:
            return f'--{self.name} / -{self.mini} => <VALUE> | {self._description}'
        return f'--{self.name} / -{self.mini} | {self._description}'

    def short(self):
        if self.value:
            return f'[--{self.name} / -{self.mini} <VALUE>]'
        else:
            return f'[--{self.name} / -{self.mini}]'

    def __call__(self, value=None):
        if isinstance(self.triggers, str):
            if value:
                set_flag(self.triggers, value)
            else:
                set_bool_flag(self.triggers, True)
        else:
            if value:
                self.triggers(value)
            else:
                self.triggers()


class ArgumentParser:
    def __init__(self, description):
        self.prog = get_flag("PROG_NAME")
        self.version = get_flag("VERSION")
        self.description = description

        self.arguments = []
        self.positionals = []
        self.flags = []

        self.satisfied = False

    def add_argument(self, arg):
        if arg.positional:
            self.positionals.append(arg)
        else:
            self.arguments.append(arg)
        return self

    def add_flag(self, flag):
        self.flags.append(flag)
        return self

    def add(self, item):
        if isinstance(item, Flag):
            self.add_flag(item)
        elif isinstance(item, Argument):
            self.add_argument(item)
        return self

    def parse_argument(self, argument: Argument, args):
        if len(args) < argument.nargs:
            if self.satisfied:
                return args
            raise Exception(f"Got {argument.nargs}, expected {len(args)}")
        _A = []
        for i in range(argument.nargs):
            _A.append(args.pop(0))
        argument(_A)

        return args

    def parse_positionals(self, args):
        for pos in self.positionals:
            args = self.parse_argument(pos, args)
        return args

    def parse_flag(self, flag, call, vals):
        val = None
        if flag.value:
            if call in vals:
                val = vals[call]
            else:
                raise Exception("Flag missing value")
            flag(val)
        else:
            flag()

        if flag.allow_end:
            self.satisfied = True

    def parse_arguments(self, args):
        H = False
        head = ""
        while len(args) != 0:
            head = args.pop(0)
            for arg in self.arguments:
                if arg.name == head:
                    args = self.parse_argument(arg, args)
                    H = True
        if H is False and head:
            args = [head] + args
        return args

    def parse_flags(self, args):
        names = []
        minis = []
        vals = {}
        for i, arg in enumerate(args):
            if arg.startswith("--"):
                key = arg[2:]
                if "=" in key:
                    key, val = key.split("=", 1)
                    vals[key] = val
                names.append(key)
            elif arg.startswith("-"):
                key = arg[1:]
                if "=" in key:
                    key, val = key.split("=", 1)
                    vals[key] = val
                minis.append(key)
        for flag in self.flags:
            if flag.name in names:
                self.parse_flag(flag, flag.name, vals)
                val = "--" + flag.name
                if flag.name in vals:
                    val += "=" + vals[flag.name]
                args.pop(args.index(val))
            if flag.mini in minis:
                self.parse_flag(flag, flag.mini, vals)
                val = "-" + flag.mini
                if flag.mini in vals:
                    val += "=" + vals[flag.mini]
                args.pop(args.index(val))

        return args

    @property
    def help(self):
        shorts = list(map(Argument.short, self.positionals))
        shorts += list(map(Argument.short, self.arguments))
        shorts += list(map(Flag.short, self.flags))

        longs_P = list(map(Argument.description, self.positionals))
        longs_A = list(map(Argument.description, self.arguments))
        longs_F = list(map(Flag.description, self.flags))
        fmt = "\n│ "
        if longs_A:
            NA = f"""├ [bold]Named Arguments[/]
│ {fmt.join(longs_A)}\n"""
        else:
            NA = ""
        if longs_P:
            NP = f"""├ [bold]Positional Arguments[/]
│ {fmt.join(longs_P)}\n"""
        else:
            NP = ""
        if longs_F:
            NF = f"""├ [bold]Flags[/]
│ {fmt.join(longs_F)}\n"""
        else:
            NF = ""
        return f"""┏  {self.prog} => {" ".join(shorts)}
┡  {self.description}\n{NA}{NP}{NF}└ END OF HELP"""

    def print_help(self):
        console.print(self.help)

    def print_version(self):
        console.print(f'{self.prog} - [yellow]V[green]{self.version}')

    def parse(self, args: list[str] = None):
        if args is None:
            args = sys.argv
        args = self.parse_flags(args)
        args = self.parse_positionals(args)
        args = self.parse_arguments(args)
        if len(args) != 0:
            raise Exception(f"Too many arguments: {len(args)}")
        return self

    __call__ = parse

    def add_help(self):
        self.add_flag(Flag("help", "h", False, self.print_help, "Get help", True))
        return self

    def add_version(self):
        self.add_flag(Flag("version", "v", False, self.print_version, "Get version", True))
        return self
