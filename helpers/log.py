import datetime
import sys
def logger(name):
    class Tee(object):
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
    f = open(f"{name}/{datetime.datetime.now().strftime(f'{name}_%H_%M_%d_%m_%Y.txt')}", 'w')
    backup = sys.stdout
    sys.stderr = Tee(sys.stdout, f)
    sys.stdout = Tee(sys.stdout, f)

