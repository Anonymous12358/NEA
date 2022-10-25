"""
Manages the loading of language files and the processing of output
"""

from collections.abc import Callable, Collection


class Language:
    def __init__(self, languages: Collection[str], print_func: Callable[[str], None]):
        self.__print_fun = print_func
        self.__lang_dict = {}
        for name in languages:
            self.__load_file(name)

    def __load_file(self, name: str):
        """
        Loads a lang file. Keys not specified in the new lang file will use the most recently loaded lang file that does
        specify them.
        :param name: The name of the file to load
        """
        try:
            with open("resources/lang/" + name + ".lang", 'r') as file:
                lines = file.readlines()
        except (FileNotFoundError, PermissionError):
            self.print_key("error.file_absent.lang", language=name)
            raise

        for line in lines:
            if line == "":
                continue

            key, sep, value = line.strip().partition("=")
            if value.endswith("^"):
                should_append_newline = False
                value = value[:-1]
            else:
                should_append_newline = True
            if value.startswith("\"") and value.endswith("\""):
                value = value[1:-1]
            if should_append_newline:
                value += "\n"

            if sep == "":
                self.print_key("warning.lang.bad_line", line=key)
            else:
                self.__lang_dict[key] = value

    def resolve_key(self, key: str, /, **kwargs: str) -> str:
        if key in self.__lang_dict:
            string = self.__lang_dict[key]
            for param, value in kwargs.items():
                string = string.replace(f"{{{param}}}", value)
            return string
        else:
            params = " ".join(f"{param}={value}" for param, value in kwargs.items())
            return f"{key} {params}"

    def print_key(self, key: str, /, **kwargs: str):
        string = self.resolve_key(key, **kwargs)

        prefix, _, _ = key.partition(".")
        if prefix == "error":
            string = self.resolve_key(".error") + string
        elif prefix == "warning":
            string = self.resolve_key(".warning") + string

        self.__print_fun(string)
