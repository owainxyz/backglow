import fcntl, glob, os, re, threading, time

i2cSlave = 0x0703
ddcAddr = 0x37
edidAddr = 0x50
page = (0xF8, 0xE1)

codes = {"strength": 0x60, "mode": 0x61, "pattern": 0x62, "fgR": 0x63, "fgG": 0x64, "fgB": 0x65, "bgR": 0x66, "bgG": 0x67, "bgB": 0x68}

strengths = ["Off", "Low", "Medium", "Strong"]
patterns = ["Red", "Green", "Blue", "Rainbow", "Custom"]
modeLists = {
    12: ["Static", "Simple Shift", "Gradient Shift", "Simple Filling", "1 Way Filling", "2 Way Filling", "Breathing", "Motion Point", "Zoom", "Discolor", "Water Wave", "Flashing", "Demo"],
    13: ["Audio", "Static", "Simple Shift", "Gradient Shift", "Simple Filling", "1 Way Filling", "2 Way Filling", "Breathing", "Motion Point", "Zoom", "Discolor", "Water Wave", "Flashing", "Demo"],
    14: ["Audio 1", "Audio 2", "Static", "Dark Point Sweep", "Gradient Shift", "Spread Fill", "Drip Fill", "Spreading Drip Fill", "Breathing", "Light Point Sweep", "Zoom", "Rainbow", "Wave", "Flashing", "Demo"],
    15: ["LoL", "Audio 1", "Audio 2", "Static", "Dark Point Sweep", "Gradient Shift", "Spread Fill", "Drip Fill", "Spreading Drip Fill", "Breathing", "Light Point Sweep", "Zoom", "Rainbow", "Wave", "Flashing", "Demo"],
    16: ["CS", "Audio 1", "Audio 2", "Static", "Dark Point Sweep", "Gradient Shift", "Spread Fill", "Drip Fill", "Spreading Drip Fill", "Breathing", "Light Point Sweep", "Zoom", "Rainbow", "Wave", "Flashing", "Demo"],
}

lock = threading.Lock()
cache = {"bus": None, "model": None}


class MonitorError(Exception):
    pass


def frame(payload):
    pkt = bytes([0x51, 0x80 | len(payload)]) + bytes(payload)
    chk = 0x6E
    for b in pkt:
        chk ^= b
    return pkt + bytes([chk])


def openBus(bus, addr):
    try:
        fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR | os.O_CLOEXEC)
    except PermissionError:
        raise MonitorError("no access")
    except OSError:
        raise MonitorError("no monitor")
    try:
        fcntl.ioctl(fd, i2cSlave, addr)
    except OSError:
        os.close(fd)
        raise MonitorError("no monitor")
    return fd


def readEdid(bus):
    try:
        fd = openBus(bus, edidAddr)
    except MonitorError:
        return None
    try:
        os.write(fd, b"\x00")
        data = os.read(fd, 128)
    except OSError:
        return None
    finally:
        os.close(fd)
    if len(data) < 128 or data[:8] != b"\x00\xff\xff\xff\xff\xff\xff\x00":
        return None
    m = (data[8] << 8) | data[9]
    vendor = "".join(chr(((m >> s) & 0x1F) + 64) for s in (10, 5, 0))
    name = ""
    for i in range(54, 126, 18):
        if data[i:i + 3] == b"\x00\x00\x00" and data[i + 3] == 0xFC:
            name = data[i + 5:i + 18].decode("ascii", "replace").strip()
    return vendor, name


def buses():
    out = []
    for p in glob.glob("/dev/i2c-*"):
        m = re.match(r"/dev/i2c-(\d+)$", p)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def transact(bus, payload, reply=True):
    with lock:
        last = MonitorError("no reply")
        for attempt in range(3):
            fd = openBus(bus, ddcAddr)
            try:
                os.write(fd, frame(payload))
                time.sleep(0.05 if reply else 0.12)
                if not reply:
                    return None
                r = os.read(fd, 16)
            except OSError:
                last = MonitorError("no reply")
                time.sleep(0.1)
                continue
            finally:
                os.close(fd)
            n = r[1] & 0x7F
            if r[0] != 0x6E or not r[1] & 0x80 or n < 8 or n + 3 > len(r):
                time.sleep(0.1)
                continue
            chk = 0x50
            for b in r[:n + 3]:
                chk ^= b
            if chk or r[2] != 0x02 or r[3] != 0x00:
                time.sleep(0.1)
                continue
            return (r[6] << 8) | r[7], (r[8] << 8) | r[9]
        raise last


def getCode(bus, code):
    return transact(bus, [0x01, page[0], page[1], code])


def setCode(bus, code, value):
    transact(bus, [0x03, page[0], page[1], code, (value >> 8) & 0xFF, value & 0xFF], reply=False)
    time.sleep(0.15)


def find():
    if cache["bus"] is not None:
        try:
            getCode(cache["bus"], codes["mode"])
            return cache["bus"], cache["model"]
        except MonitorError:
            cache["bus"] = None
    denied = False
    for bus in buses():
        if not os.access(f"/dev/i2c-{bus}", os.R_OK | os.W_OK):
            denied = True
            continue
        edid = readEdid(bus)
        if not edid or edid[0] != "AOC":
            continue
        try:
            getCode(bus, codes["mode"])
        except MonitorError:
            continue
        cache["bus"], cache["model"] = bus, edid[1]
        return bus, edid[1]
    raise MonitorError("no access" if denied else "no monitor")


def read():
    bus, model = find()
    out = {"model": model, "bus": bus}
    for key, code in codes.items():
        top, cur = getCode(bus, code)
        out[key] = cur
        if key == "mode":
            out["modes"] = modeLists.get(top, [f"Mode {i}" for i in range(top + 1)])
    out["strengths"] = strengths
    out["patterns"] = patterns
    return out


def write(key, value):
    if key not in codes:
        raise MonitorError("bad key")
    bus, _ = find()
    top, _ = getCode(bus, codes[key])
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= top:
        raise MonitorError("bad value")
    setCode(bus, codes[key], value)


def toPercent(hexColour):
    return [round(int(hexColour[i:i + 2], 16) * 100 / 255) for i in (1, 3, 5)]


def setColour(hexColour, which="bg"):
    r, g, b = toPercent(hexColour)
    for ch, v in zip("RGB", (r, g, b)):
        write(which + ch, v)
