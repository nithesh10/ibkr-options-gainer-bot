import datetime
import os
import sys

class Tee(object):
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
def logger(name):
    f = open(f"{name}/{datetime.datetime.now().strftime(f'{name}_%H_%M_%d_%m_%Y.txt')}", 'w')
    backup = sys.stdout
    sys.stderr = Tee(sys.stdout, f)
    sys.stdout = Tee(sys.stdout, f)

def logger_f(fname):
    log_dir = 'storage/logs'
    log_file_path = os.path.join(log_dir, fname)

    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    f = open(f"storage/logs/{fname}/{datetime.datetime.now().strftime('mylogfile_%H_%M_%d_%m_%Y.txt')}", 'w')
    backup = sys.stdout
    sys.stderr = Tee(sys.stdout, f)
    sys.stdout = Tee(sys.stdout, f)
