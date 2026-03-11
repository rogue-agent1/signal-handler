#!/usr/bin/env python3
"""signal_handler - Unix signal handling simulator (signal delivery, masking, pending queue).

Usage: python signal_handler.py [--demo]
"""
import sys
from collections import deque
from enum import IntEnum

class Signal(IntEnum):
    SIGHUP = 1; SIGINT = 2; SIGQUIT = 3; SIGILL = 4; SIGTRAP = 5
    SIGABRT = 6; SIGBUS = 7; SIGFPE = 8; SIGKILL = 9; SIGUSR1 = 10
    SIGSEGV = 11; SIGUSR2 = 12; SIGPIPE = 13; SIGALRM = 14; SIGTERM = 15
    SIGCHLD = 17; SIGCONT = 18; SIGSTOP = 19; SIGTSTP = 20

class SigAction:
    DEFAULT = "default"
    IGNORE = "ignore"
    def __init__(self, handler=None):
        self.handler = handler or self.DEFAULT

class SignalState:
    def __init__(self):
        self.handlers = {}
        self.mask = set()  # Blocked signals
        self.pending = set()  # Pending (blocked but received)
        self.queue = deque()  # Delivery queue
        self.log = []
        self._default_fatal = {Signal.SIGKILL, Signal.SIGINT, Signal.SIGTERM,
                               Signal.SIGQUIT, Signal.SIGSEGV, Signal.SIGABRT,
                               Signal.SIGBUS, Signal.SIGFPE, Signal.SIGILL}
        self._uncatchable = {Signal.SIGKILL, Signal.SIGSTOP}
        self.alive = True

    def signal(self, sig, handler):
        if sig in self._uncatchable:
            self._log(f"Cannot change handler for {sig.name}")
            return False
        self.handlers[sig] = SigAction(handler)
        self._log(f"Set handler for {sig.name}: {handler}")
        return True

    def mask_signal(self, sig):
        if sig in self._uncatchable:
            self._log(f"Cannot mask {sig.name}")
            return False
        self.mask.add(sig)
        self._log(f"Masked {sig.name}")
        return True

    def unmask_signal(self, sig):
        self.mask.discard(sig)
        self._log(f"Unmasked {sig.name}")
        if sig in self.pending:
            self.pending.discard(sig)
            self.queue.append(sig)
            self._log(f"Delivering pending {sig.name}")
        return True

    def send(self, sig):
        if not self.alive:
            self._log(f"Process dead, cannot deliver {sig.name}")
            return
        self._log(f"Received {sig.name}")
        if sig in self.mask and sig not in self._uncatchable:
            self.pending.add(sig)
            self._log(f"  → blocked, now pending")
            return
        self.queue.append(sig)

    def deliver(self):
        delivered = []
        while self.queue and self.alive:
            sig = self.queue.popleft()
            action = self.handlers.get(sig, SigAction())
            if action.handler == SigAction.IGNORE:
                self._log(f"Delivered {sig.name} → ignored")
            elif action.handler == SigAction.DEFAULT:
                if sig in self._default_fatal:
                    self._log(f"Delivered {sig.name} → default (FATAL)")
                    self.alive = False
                    delivered.append((sig, "fatal"))
                    break
                else:
                    self._log(f"Delivered {sig.name} → default (no-op)")
            elif callable(action.handler):
                self._log(f"Delivered {sig.name} → handler")
                action.handler(sig)
            delivered.append((sig, action.handler))
        return delivered

    def _log(self, msg):
        self.log.append(msg)

    def status(self):
        return {
            "alive": self.alive,
            "masked": {s.name for s in self.mask},
            "pending": {s.name for s in self.pending},
            "queued": len(self.queue),
            "handlers": {s.name: a.handler if not callable(a.handler) else f"fn@{a.handler.__name__}"
                        for s, a in self.handlers.items()},
        }

def main():
    print("=== Unix Signal Handling Simulator ===\n")
    ss = SignalState()

    # Install handlers
    caught = []
    def my_handler(sig):
        caught.append(sig)
        print(f"    [handler] Caught {sig.name}!")

    ss.signal(Signal.SIGINT, my_handler)
    ss.signal(Signal.SIGUSR1, my_handler)
    ss.signal(Signal.SIGTERM, SigAction.IGNORE)
    ss.signal(Signal.SIGKILL, my_handler)  # Should fail

    # Mask SIGUSR2
    ss.mask_signal(Signal.SIGUSR2)

    print("Sending signals:")
    ss.send(Signal.SIGINT)
    ss.send(Signal.SIGTERM)  # Ignored
    ss.send(Signal.SIGUSR1)
    ss.send(Signal.SIGUSR2)  # Blocked
    ss.deliver()

    print(f"\nCaught: {[s.name for s in caught]}")
    print(f"Status: {ss.status()}")

    # Unmask SIGUSR2 — should deliver pending
    print(f"\nUnmasking SIGUSR2:")
    ss.signal(Signal.SIGUSR2, my_handler)
    ss.unmask_signal(Signal.SIGUSR2)
    ss.deliver()
    print(f"Caught now: {[s.name for s in caught]}")

    # SIGKILL is always fatal
    print(f"\nSending SIGKILL:")
    ss.send(Signal.SIGKILL)
    ss.deliver()
    print(f"Alive: {ss.alive}")

    print(f"\nFull log:")
    for entry in ss.log:
        print(f"  {entry}")

if __name__ == "__main__":
    main()
