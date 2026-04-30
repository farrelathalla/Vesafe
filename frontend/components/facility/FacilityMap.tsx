import type { Route } from "next";
import Link from "next/link";

import type { Facility } from "@/types";

export function FacilityList({ facilities }: { facilities: Facility[] }) {
  return (
    <div className="panel">
      <div className="eyebrow">Fasilitas Terdaftar</div>
      <h2 style={{ marginTop: 8 }}>Daftar fasilitas</h2>
      <div className="card-grid" style={{ marginTop: 20 }}>
        {facilities.map((facility) => (
          <Link className="feed-card" href={`/facility/${facility.facility_id}` as Route} key={facility.facility_id}>
            <div className="eyebrow">{facility.address}</div>
            <h3 style={{ marginBottom: 8 }}>{facility.name}</h3>
            <p className="muted" style={{ margin: 0 }}>
              Upload foto, bangun world model 3D, jalankan analisis K3.
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
