"""Stage cache: rebuild and re-export only what changed.

A part's key is a sha256 over everything its builder can read:
  - the source bytes of each dependency module, plus that module's UPPERCASE globals (constants imported into it);
  - the builder's arguments;
  - extra input files (e.g. traced DXFs);
  - the build123d version.
If the key matches a cached `.brep`, the part is loaded instead of rebuilt. An export manifest records the key each
output file was written from, so a file whose part did not change is not rewritten.

Arguments must be plain data (dict, list, tuple, str, int, float, bool, None, numpy arrays, shapely geometry).
Anything else raises TypeError: a value the key cannot see would make the cache unsafe, so it is refused, not guessed.

Used by projects/SurgicalDrillGuide/macros/surgical_drill_guide.py. See docs/cad_method.md, "A stage cache".
"""
import hashlib
import inspect
import json
import struct
from pathlib import Path

CACHE_VERSION = 1


def _canon(obj, h):
    """Feed a canonical, type-tagged encoding of obj into hash h."""
    if obj is None:
        h.update(b"N")
    elif isinstance(obj, bool):
        h.update(b"B1" if obj else b"B0")
    elif isinstance(obj, int):
        h.update(b"I" + str(obj).encode())
    elif isinstance(obj, float):
        h.update(b"F" + struct.pack("<d", obj))
    elif isinstance(obj, str):
        h.update(b"S" + str(len(obj)).encode() + b":" + obj.encode("utf-8"))
    elif isinstance(obj, (list, tuple)):
        h.update(b"L" if isinstance(obj, list) else b"T")
        h.update(str(len(obj)).encode() + b"[")
        for x in obj:
            _canon(x, h)
        h.update(b"]")
    elif isinstance(obj, dict):
        h.update(b"D" + str(len(obj)).encode() + b"{")
        for k in sorted(obj, key=repr):
            _canon(k, h)
            _canon(obj[k], h)
        h.update(b"}")
    elif type(obj).__module__.startswith("numpy"):
        import numpy as np
        a = np.asarray(obj)
        h.update(b"A" + str(a.dtype).encode() + str(a.shape).encode() + np.ascontiguousarray(a).tobytes())
    elif type(obj).__module__.startswith("shapely"):
        h.update(b"G" + obj.wkb)
    else:
        raise TypeError(f"stage_cache: cannot key a {type(obj).__module__}.{type(obj).__name__}")


def _module_part(mod, h):
    h.update(b"M" + mod.__name__.encode())
    h.update(Path(inspect.getsourcefile(mod)).read_bytes())
    consts = {k: v for k, v in vars(mod).items() if k.isupper() and not k.startswith("_")}
    for k in sorted(consts):
        v = consts[k]
        if isinstance(v, Path):
            v = str(v)
        try:
            _canon(k, h)
            _canon(v, h)
        except TypeError:
            raise TypeError(f"stage_cache: constant {mod.__name__}.{k} is a {type(v).__name__}, which cannot be keyed")


def fingerprint(modules, args=(), files=()):
    """Key over dependency modules (source + UPPERCASE globals), builder arguments and input files."""
    import build123d
    h = hashlib.sha256()
    h.update(f"stage_cache v{CACHE_VERSION} build123d {build123d.__version__}".encode())
    for m in sorted(modules, key=lambda m: m.__name__):
        _module_part(m, h)
    _canon(list(args), h)
    for f in sorted(Path(f) for f in files):
        h.update(b"P" + f.name.encode() + f.read_bytes())
    return h.hexdigest()


class Cache:
    """Load-or-build store of shapes in `folder`, plus an export manifest."""

    def __init__(self, folder, enabled=True):
        self.folder = Path(folder)
        self.enabled = enabled
        self.folder.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.folder / "exports.json"
        try:
            self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.manifest = {}
        self.rebuilt, self.loaded, self.written, self.skipped = [], [], [], []

    def shape(self, name, key, build):
        """Return build()'s result, from cache when `key` matches. build() returns (shape, side_data_json_ok)."""
        from build123d import export_brep, import_brep
        brep = self.folder / f"{name}_{key[:16]}.brep"
        side = brep.with_suffix(".json")
        if self.enabled and brep.exists() and side.exists():
            self.loaded.append(name)
            return import_brep(str(brep)), json.loads(side.read_text(encoding="utf-8"))
        shp, data = build()
        self.rebuilt.append(name)
        export_brep(shp, str(brep))
        side.write_text(json.dumps(data), encoding="utf-8")
        return shp, data

    def needs_write(self, path, key):
        """True when `path` is missing or was last written from a different key (always True with the cache off)."""
        p = str(Path(path).resolve())
        return not self.enabled or not Path(path).exists() or self.manifest.get(p) != key

    def wrote(self, path, key):
        self.manifest[str(Path(path).resolve())] = key
        self.written.append(Path(path).name)

    def skip(self, path):
        self.skipped.append(Path(path).name)

    def save(self):
        self.manifest_path.write_text(json.dumps(self.manifest, indent=1, sort_keys=True), encoding="utf-8")

    def summary(self):
        return (f"cache: rebuilt {self.rebuilt or 'none'}; from cache {self.loaded or 'none'}; "
                f"written {len(self.written)} file(s); unchanged, not rewritten {len(self.skipped)}")
