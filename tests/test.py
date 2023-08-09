from ibapi.client import *
from ibapi.wrapper import *
import sys
from pathlib import Path

current_path = Path.cwd()
print(current_path)
port = 7497
class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
    def nextValidId(self, orderId: int):
        self.reqScannerParameters()
    def scannerParameters(self, xml):
        dir = f"{current_path}//scanner.xml"
        open(dir, 'w').write(xml)
        
        print("Scanner parameters received!")
app = TestApp()
app.connect("127.0.0.1", port, 1001)
app.run()