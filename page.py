class page():
    def __init__(self, applications):
        self.applications = applications
    def setSessions(self, session):
        self.sessions = session
    def __repr__(self):
        return "page(" + self.applications.__str__() + ")"