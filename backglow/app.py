import base64, hashlib, json, os, re, sys, threading

from . import __version__, monitor

webDir = os.path.join(os.path.dirname(__file__), "web")
hexColour = re.compile(r"^#[0-9a-fA-F]{6}$")
fields = ("strength", "mode", "pattern")


def errorText(e):
    return {"no access": "No access", "no monitor": "No monitor", "no reply": "No reply", "bad value": "Bad value", "bad key": "Bad value"}.get(str(e), "Failed")


class Api:
    def __init__(self):
        self._window = None
        self._pending = {}
        self._cond = threading.Condition()
        threading.Thread(target=self._writer, daemon=True).start()

    def state(self):
        try:
            return {"version": __version__, "monitor": monitor.read()}
        except monitor.MonitorError as e:
            return {"version": __version__, "monitor": None, "error": errorText(e)}

    def set(self, key, value):
        if key not in fields or not isinstance(value, int) or isinstance(value, bool):
            return {"error": "Bad value"}
        self._queue(key, lambda: monitor.write(key, value))
        return {"ok": True}

    def colour(self, which, value):
        if which not in ("fg", "bg") or not isinstance(value, str) or not hexColour.match(value):
            return {"error": "Bad value"}
        self._queue(which, lambda: monitor.setColour(value, which))
        return {"ok": True}

    def _queue(self, key, job):
        with self._cond:
            self._pending.pop(key, None)
            self._pending[key] = job
            self._cond.notify()

    def _writer(self):
        while True:
            with self._cond:
                while not self._pending:
                    self._cond.wait()
                key = next(iter(self._pending))
                job = self._pending.pop(key)
            try:
                job()
            except monitor.MonitorError as e:
                if self._window:
                    self._window.evaluate_js(f"window.onWriteError && window.onWriteError({json.dumps(errorText(e))})")


def page():
    def read(name):
        with open(os.path.join(webDir, name), encoding="utf-8") as f:
            return f.read()

    script = read("app.js")
    scriptHash = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    csp = "; ".join([
        "default-src 'none'",
        f"script-src 'sha256-{scriptHash}' 'unsafe-eval'",
        "style-src 'unsafe-inline'",
        "img-src data:",
        "connect-src 'none'",
        "object-src 'none'",
        "frame-src 'none'",
        "form-action 'none'",
        "base-uri 'none'",
    ])
    html = read("index.html")
    html = html.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{csp}">', 1)
    html = html.replace('<link rel="stylesheet" href="style.css">', "<style>" + read("style.css") + "</style>", 1)
    html = html.replace('<script src="app.js"></script>', "<script>" + script + "</script>", 1)
    return html


def gui():
    import webview
    api = Api()
    api._window = webview.create_window("backglow", html=page(), js_api=api, width=1060, height=720, min_size=(640, 480), background_color="#0a0a0a", text_select=False)
    webview.start(gui="gtk", debug=False, private_mode=True)


def pick(options, text):
    t = text.strip().lower().replace("-", " ")
    if t.isdigit() and int(t) < len(options):
        return int(t)
    for i, o in enumerate(options):
        if o.lower() == t:
            return i
    sys.exit("options: " + ", ".join(o.lower() for o in options))


def cli(args):
    try:
        state = monitor.read()
        if args[0] == "--status":
            print(f"{state['model']}  {state['strengths'][state['strength']].lower()}  {state['modes'][state['mode']].lower()}  {state['patterns'][state['pattern']].lower()}  {state['bg']}")
            return
        if len(args) < 2:
            sys.exit(usage)
        flag, value = args[0], args[1]
        if flag == "--mode":
            monitor.write("mode", pick(state["modes"], value))
        elif flag == "--strength":
            monitor.write("strength", pick(state["strengths"], value))
        elif flag == "--pattern":
            monitor.write("pattern", pick(state["patterns"], value))
        elif flag in ("--colour", "--color", "--colour2"):
            value = value if value.startswith("#") else "#" + value
            if not hexColour.match(value):
                sys.exit("colour is #rrggbb")
            monitor.write("pattern", state["patterns"].index("Custom"))
            monitor.setColour(value, "fg" if flag == "--colour2" else "bg")
        else:
            sys.exit(usage)
    except monitor.MonitorError as e:
        sys.exit(str(e))


usage = "usage: backglow\n       backglow --status\n       backglow --mode <name|n>\n       backglow --strength off|low|medium|strong\n       backglow --pattern red|green|blue|rainbow|custom\n       backglow --colour <#rrggbb>\n       backglow --colour2 <#rrggbb>"


def main():
    args = sys.argv[1:]
    if not args:
        gui()
    elif args[0] in ("-h", "--help"):
        print(usage)
    elif args[0] in ("-V", "--version"):
        print(__version__)
    else:
        cli(args)
