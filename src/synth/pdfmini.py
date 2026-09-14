"""Minimaler PDF-Writer ohne Abhängigkeiten: Text (Helvetica, Courier), Linien, gefüllte Rechtecke, mehrere Seiten.
Reicht für Rechnungen mit Textebene. Umlaute über WinAnsiEncoding. Für 'Scans' siehe scan() unten (braucht pypdfium2 und Pillow,
beide kommen mit pdfplumber).
"""
from pathlib import Path

FONTS = {"H": "Helvetica", "HB": "Helvetica-Bold", "HI": "Helvetica-Oblique", "C": "Courier", "CB": "Courier-Bold"}
A4 = (595, 842)


def _esc(s):
    return s.encode("cp1252", errors="replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class Doc:
    def __init__(self):
        self.pages = []

    def page(self):
        self.pages.append([]); return self

    def text(self, x, y, s, size=9, font="H", gray=0.0):
        """x, y in Punkten von links unten."""
        self.pages[-1].append(f"BT {gray:.2f} g /{font} {size} Tf {x:.1f} {y:.1f} Td ({_esc(s)}) Tj ET")

    def text_right(self, x_right, y, s, size=9, font="H", gray=0.0):
        w = len(s) * size * (0.6 if font.startswith("C") else 0.5)
        self.text(x_right - w, y, s, size, font, gray)

    def line(self, x1, y1, x2, y2, w=0.5, gray=0.0):
        self.pages[-1].append(f"{gray:.2f} G {w} w {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S")

    def rect(self, x, y, w, h, fill=(1, 1, 0), stroke=False):
        r, g, b = fill
        self.pages[-1].append(f"{r} {g} {b} rg {x:.1f} {y:.1f} {w:.1f} {h:.1f} re {'B' if stroke else 'f'} 0 g")

    def box(self, x, y, w, h, gray=0.0):
        self.pages[-1].append(f"{gray:.2f} G 0.5 w {x:.1f} {y:.1f} {w:.1f} {h:.1f} re S")

    def save(self, path):
        objs = []  # (num, bytes)
        font_objs = {}
        n = 3 + len(self.pages) * 2
        for i, (k, name) in enumerate(FONTS.items()):
            font_objs[k] = n + i
        objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(len(self.pages)))
        objs.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(self.pages)} >>".encode())
        fres = " ".join(f"/{k} {v} 0 R" for k, v in font_objs.items())
        for i, ops in enumerate(self.pages):
            content = "\n".join(ops).encode("latin-1")
            objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {A4[0]} {A4[1]}] /Resources << /Font << {fres} >> >> /Contents {4 + 2 * i} 0 R >>".encode())
            objs.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
        for k, name in FONTS.items():
            objs.append(f"<< /Type /Font /Subtype /Type1 /BaseFont /{name} /Encoding /WinAnsiEncoding >>".encode())
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets = []
        for i, o in enumerate(objs, 1):
            offsets.append(len(out)); out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
        for off in offsets: out += f"{off:010d} 00000 n \n".encode()
        out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
        Path(path).write_bytes(bytes(out))


def scan(src, dst, seed=0, dpi=150, rotate=0.4, noise=12, contrast=0.85):
    """Aus einem Text-PDF ein Bild-PDF ohne Textebene machen: leicht gedreht, körnig, grau. Wie ein Scan."""
    import random
    import pypdfium2 as pdfium
    from PIL import Image, ImageEnhance, ImageFilter
    rng = random.Random(seed)
    pdf = pdfium.PdfDocument(str(src)); imgs = []
    for i in range(len(pdf)):
        im = pdf[i].render(scale=dpi / 72).to_pil().convert("L")
        im = ImageEnhance.Contrast(im).enhance(contrast)
        im = im.rotate(rng.uniform(-rotate, rotate), resample=Image.BILINEAR, fillcolor=255, expand=False)
        px = im.load(); w, h = im.size
        for _ in range(int(w * h * 0.002)):
            x, y = rng.randrange(w), rng.randrange(h); px[x, y] = max(0, px[x, y] - rng.randint(0, noise * 8))
        im = im.filter(ImageFilter.GaussianBlur(0.6))
        imgs.append(im.convert("L"))
    imgs[0].save(str(dst), save_all=True, append_images=imgs[1:], resolution=dpi)
