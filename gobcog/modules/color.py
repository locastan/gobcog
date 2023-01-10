

class Color:
    darkgrey = "[2;30m"
    red = "[2;31m"
    yellow = "[2;32m"
    orange = "[2;33m"
    blue = "[2;34m"
    pink = "[2;35m"
    green = "[2;36m"
    white = "[2;37m"
    none = "[0m"

    @staticmethod
    def get_color(item):
        if item[0] == ".":
            return Color.blue + item + Color.none
        elif item[0] == "[":
            return Color.orange + item + Color.none
        elif item[0] == "{":
            return Color.green + item + Color.none
        else:
            return Color.yellow + item + Color.none
