import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// CRC32 lookup table — used by ZIP format
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[i] = c;
  }
  return t;
})();

function crc32(buf: Buffer): number {
  let crc = 0xffffffff;
  for (const byte of buf) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function u16(n: number): Buffer {
  const b = Buffer.alloc(2);
  b.writeUInt16LE(n, 0);
  return b;
}

function u32(n: number): Buffer {
  const b = Buffer.alloc(4);
  b.writeUInt32LE(n >>> 0, 0);
  return b;
}

// Minimal STORED (uncompressed) ZIP builder — no external dependencies
function buildZip(files: { name: string; data: Buffer }[]): Buffer {
  const locals: Buffer[] = [];
  const central: Buffer[] = [];
  let offset = 0;

  for (const file of files) {
    const name = Buffer.from(file.name, "utf8");
    const crc = crc32(file.data);
    const size = file.data.length;

    const local = Buffer.concat([
      Buffer.from([0x50, 0x4b, 0x03, 0x04]),
      u16(20), u16(0), u16(0),
      u16(0), u16(0),
      u32(crc), u32(size), u32(size),
      u16(name.length), u16(0),
      name,
    ]);

    central.push(Buffer.concat([
      Buffer.from([0x50, 0x4b, 0x01, 0x02]),
      u16(20), u16(20), u16(0), u16(0),
      u16(0), u16(0),
      u32(crc), u32(size), u32(size),
      u16(name.length), u16(0), u16(0),
      u16(0), u16(0), u32(0), u32(offset),
      name,
    ]));

    offset += local.length + size;
    locals.push(local, file.data);
  }

  const cd = Buffer.concat(central);
  const eocd = Buffer.concat([
    Buffer.from([0x50, 0x4b, 0x05, 0x06]),
    u16(0), u16(0),
    u16(files.length), u16(files.length),
    u32(cd.length), u32(offset),
    u16(0),
  ]);

  return Buffer.concat([...locals, cd, eocd]);
}

export async function GET() {
  const dir = path.join(process.cwd(), "public", "sample-photos");

  if (!fs.existsSync(dir)) {
    return NextResponse.json({ error: "Sample photos folder not found." }, { status: 404 });
  }

  const IMAGE_EXTS = new Set([".jpg", ".jpeg", ".png", ".webp"]);
  const filenames = fs
    .readdirSync(dir)
    .filter((f) => IMAGE_EXTS.has(path.extname(f).toLowerCase()))
    .sort();

  if (filenames.length === 0) {
    return NextResponse.json(
      { error: "No sample photos in folder yet. Generate them using PHOTO_CAPTURE_GUIDE.md and place them in frontend/public/sample-photos/." },
      { status: 404 }
    );
  }

  const files = filenames.map((name) => ({
    name,
    data: fs.readFileSync(path.join(dir, name)),
  }));

  const zip = buildZip(files);

  return new NextResponse(zip, {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="vesafe-sample-photos.zip"`,
      "Content-Length": String(zip.length),
    },
  });
}
