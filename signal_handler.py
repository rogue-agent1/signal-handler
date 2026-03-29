#!/usr/bin/env python3
"""Signal handler utility. Zero dependencies."""
import signal, sys, os, functools

class SignalHandler:
    def __init__(self):
        self.handlers = {}
        self.received = []

    def on(self, sig, callback):
        if isinstance(sig, str):
            sig = getattr(signal, f"SIG{sig.upper()}", None)
            if sig is None: raise ValueError(f"Unknown signal: {sig}")
        self.handlers.setdefault(sig, []).append(callback)
        signal.signal(sig, self._dispatch)
        return self

    def _dispatch(self, signum, frame):
        self.received.append(signum)
        for cb in self.handlers.get(signum, []):
            cb(signum, frame)

    def ignore(self, sig):
        if isinstance(sig, str): sig = getattr(signal, f"SIG{sig.upper()}")
        signal.signal(sig, signal.SIG_IGN)

    def reset(self, sig):
        if isinstance(sig, str): sig = getattr(signal, f"SIG{sig.upper()}")
        signal.signal(sig, signal.SIG_DFL)

    def timeout(self, seconds):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                def handler(s, f): raise TimeoutError(f"{func.__name__} timed out")
                old = signal.signal(signal.SIGALRM, handler)
                signal.alarm(seconds)
                try:
                    return func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old)
            return wrapper
        return decorator

if __name__ == "__main__":
    sh = SignalHandler()
    received = []
    sh.on("USR1", lambda s, f: received.append(s))
    os.kill(os.getpid(), signal.SIGUSR1)
    print(f"Received {len(received)} signals")
