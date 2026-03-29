import os, signal
from signal_handler import SignalHandler
sh = SignalHandler()
received = []
sh.on("USR1", lambda s, f: received.append(s))
os.kill(os.getpid(), signal.SIGUSR1)
assert len(received) == 1
assert received[0] == signal.SIGUSR1
assert signal.SIGUSR1 in sh.received
import time
@sh.timeout(2)
def fast(): return 42
assert fast() == 42
print("signal_handler tests passed")
