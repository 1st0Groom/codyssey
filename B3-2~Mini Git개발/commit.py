import time


class Commit:
    next_id = 1

    def __init__(self, message, author, parents, branch=None):
        self.hash = f"c{Commit.next_id:04d}"

        Commit.next_id += 1

        self.message = message
        self.author = author

        self.parents = parents
        self.branch = branch

        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def __str__(self):
        return f"{self.hash} {self.message}"
