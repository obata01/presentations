
class Input:
    def __init__(self, data):
        self.data = data
        self.rows = [str(d) for d in data.split("\n") if d]

    def input(self):
        return self.rows.pop(0)
