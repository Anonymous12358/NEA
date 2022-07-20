# TODO Refactor everything to pass a language object around rather than mutable global state... maybe
_lang_dict = {}


def load_file(name: str):
    """
    Loads a lang file. Keys not specified in the new lang file will use the most recently loaded lang file that does
    specify them.
    :param name: The name of the file to load.
    """
    try:
        with open("../../resources/lang/" + name + ".lang", 'r') as file:
            lines = file.readlines()
    except (FileNotFoundError, PermissionError):
        print_key("error.file_absent.lang")
        raise

    for line in lines:
        key, sep, value = line.strip().partition("=")
        if sep == "":
            print_key("warning.lang.bad_line", line=key)
        _lang_dict[key] = value


def resolve_key(key: str, **kwargs: str) -> str:
    if key in _lang_dict:
        string = _lang_dict[key]
        for param, value in kwargs.items():
            string = string.replace(f"{{{param}}}", value)
        return string
    else:
        params = " ".join(f"{param}={value}" for param, value in kwargs.items())
        return f"{key} {params}"


def print_key(key: str, **kwargs: str):
    string = resolve_key(key, **kwargs)

    prefix, _, _ = key.partition(".")
    if prefix == "error":
        string = "##ERROR## " + string
    elif prefix == "warning":
        string = "~WARNING~ " + string

    print(string)
