import crayons


class Logger:
    def __init__(
        self,
        log_name=None,
        info_color=crayons.white,
        debug_color=crayons.blue,
        err_color=crayons.red,
    ):
        self.log_name = log_name
        self.color_map = {"DEBUG": debug_color, "ERROR": err_color, "INFO": info_color}

    @property
    def info_color(self):
        return self.color_map["INFO"]

    @info_color.setter
    def info_color(self, info_color):
        self.color_map["INFO"] = info_color

    def _log(self, args, level: str):
        if not args:
            print()
        color = self.color_map[level]
        if self.log_name is None:
            print(color(f'|{level}| {" ".join(map(str, args))}'))
        else:
            print(color(f'|{level}| |{self.log_name}| {" ".join(map(str, args))}'))

    def info(self, *args):
        self._log(args, "INFO")

    def debug(self, *args):
        self._log(args, "DEBUG")

    def err(self, *args):
        self._log(args, "ERROR")

    def cmd_debug(self, cmd, *args):
        if args:
            self._log([*args, ": $", *cmd], "DEBUG")
        else:
            self._log(["$", *cmd], "DEBUG")

    def cmd_info(self, cmd, *args):
        if args:
            self._log([*args, ": $", *cmd], "INFO")
        else:
            self._log(["$", *cmd], "INFO")
