"use client";

import { useMemo, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import * as tus from "tus-js-client";

import { buildApiUrl } from "@/lib/runtime";

function SamplePhotoDownload() {
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  async function download() {
    setStatus("loading");
    setErrorMsg("");
    try {
      const res = await fetch("/api/sample-photos/download");
      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        throw new Error((json as { error?: string }).error ?? "Download gagal");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "vesafe-sample-photos.zip";
      a.click();
      URL.revokeObjectURL(url);
      setStatus("idle");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Download gagal");
      setStatus("error");
    }
  }

  return (
    <div style={{ marginBottom: 16 }}>
      <button
        className="button secondary"
        type="button"
        disabled={status === "loading"}
        onClick={download}
        style={{ fontSize: 13 }}
      >
        {status === "loading" ? "Mengunduh..." : "Download Sample Photos"}
      </button>
      {status === "error" && (
        <p className="muted" style={{ fontSize: 12, marginTop: 6, color: "var(--critical)" }}>
          {errorMsg}
        </p>
      )}
      <p className="muted" style={{ fontSize: 11, marginTop: 4 }}>
        Download 16 foto contoh fasilitas farmasi (dengan pelanggaran K3) untuk diupload ke sini.
      </p>
    </div>
  );
}

type FileStatus = { name: string; percent: number; done: boolean; error?: string };

export function SupplementalUpload({ facilityId }: { facilityId: string }) {
  const [files, setFiles] = useState<FileStatus[]>([]);
  const endpoint = useMemo(() => buildApiUrl("/api/upload/supplemental"), []);
  const activeUploads = useRef<Map<string, tus.Upload>>(new Map());

  function updateFile(name: string, patch: Partial<FileStatus>) {
    setFiles((prev) =>
      prev.map((f) => (f.name === name ? { ...f, ...patch } : f))
    );
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] },
    multiple: true,
    maxFiles: 20,
    onDrop: (dropped) => {
      const next: FileStatus[] = dropped.map((f) => ({ name: f.name, percent: 0, done: false }));
      setFiles((prev) => {
        const existing = new Set(prev.map((f) => f.name));
        return [...prev, ...next.filter((f) => !existing.has(f.name))];
      });

      dropped.forEach((file) => {
        if (activeUploads.current.has(file.name)) return;
        const upload = new tus.Upload(file, {
          endpoint,
          retryDelays: [0, 1000, 3000],
          metadata: {
            facility_id: facilityId,
            filename: file.name,
            filetype: file.type || "image/jpeg",
          },
          onProgress: (sent, total) => {
            const percent = Math.round((sent / Math.max(total, 1)) * 100);
            updateFile(file.name, { percent });
          },
          onSuccess: () => {
            updateFile(file.name, { percent: 100, done: true });
            activeUploads.current.delete(file.name);
          },
          onError: (err) => {
            updateFile(file.name, { error: err.message });
            activeUploads.current.delete(file.name);
          },
        });
        activeUploads.current.set(file.name, upload);
        upload.start();
      });
    },
  });

  const pending = files.filter((f) => !f.done && !f.error);
  const done = files.filter((f) => f.done);
  const errors = files.filter((f) => !!f.error);

  return (
    <div className="panel">
      <div className="eyebrow">Upload Foto Fasilitas</div>
      <SamplePhotoDownload />
      <div
        className="upload-zone"
        {...getRootProps()}
        style={{ borderColor: isDragActive ? "var(--accent)" : undefined, cursor: "pointer" }}
      >
        <input {...getInputProps()} />
        <div>
          <h3 style={{ marginTop: 0 }}>Tambah foto area fasilitas</h3>
          <p className="muted">
            Unggah foto interior fasilitas farmasi — ruang produksi steril, area penyimpanan B3,
            jalur forklift, gowning room, atau area tanggap darurat.
            Foto akan diklasifikasi otomatis dan dimasukkan ke dalam world model untuk analisis K3.
          </p>
          <p className="muted" style={{ fontSize: 12 }}>
            Didukung: JPG, PNG, WebP &nbsp;·&nbsp; Maks 20 file per sesi
          </p>
          <button className="button" type="button">
            {isDragActive ? "Lepas untuk unggah" : "Pilih foto"}
          </button>
        </div>
      </div>

      {files.length > 0 && (
        <div style={{ marginTop: 16, display: "grid", gap: 6 }}>
          {pending.map((f) => (
            <div key={f.name} style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ flex: 1, background: "var(--border)", borderRadius: 4, height: 4, overflow: "hidden" }}>
                <div style={{ width: `${f.percent}%`, height: "100%", background: "var(--accent)", transition: "width 0.2s" }} />
              </div>
              <span className="muted" style={{ minWidth: 36 }}>{f.percent}%</span>
              <span style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</span>
            </div>
          ))}
          {done.length > 0 && (
            <p className="muted" style={{ fontSize: 12, margin: 0 }}>
              {done.length} foto berhasil diunggah dan sedang diproses ke world model.
            </p>
          )}
          {errors.map((f) => (
            <p key={f.name} style={{ fontSize: 12, color: "var(--critical)", margin: 0 }}>
              Gagal: {f.name} — {f.error}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
