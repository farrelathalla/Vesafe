export const DOMAIN_COLORS = {
  ICA: "#C0392B",  // Red — Pencegahan Kontaminasi
  MSA: "#D68910",  // Amber — Penanganan B3
  FRA: "#E67E22",  // Orange — Keselamatan Alat Berat
  ERA: "#C0392B",  // Red — Tanggap Darurat
  PFA: "#0D7E78",  // Teal — Alur Produksi
  SCA: "#5B2C8D",  // Purple — Komunikasi K3
} as const;

export const DOMAIN_LABELS = {
  ICA: "Pencegahan Kontaminasi",
  MSA: "Penanganan B3",
  FRA: "Keselamatan Alat Berat",
  ERA: "Tanggap Darurat",
  PFA: "Alur Produksi",
  SCA: "Komunikasi K3",
} as const;

export const SEVERITY_SIZES = {
  CRITICAL: 1.4,  // Billboard scale multiplier
  HIGH: 1.0,
  ADVISORY: 0.7,
} as const;
