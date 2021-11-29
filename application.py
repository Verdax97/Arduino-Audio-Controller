from comtypes import dispid


class application():
    def __init__(self, name, exe, logo):
        self.name = name
        self.exe = exe
        self.logo = logo
    
    def display(self):
        return "application(\"" + self.name + "\", \"" + self.exe + "\", \"" + self.logo + "\")"
    def __repr__(self):
        return self.display()