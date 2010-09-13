from backend.options import SettingsOptions


class Options(SettingsOptions):
    optFlags = [
        ["install", "i", "Execute the MySQL initialization code on the master DB."],
    ]