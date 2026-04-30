import type { Route } from "next";
import Link from "next/link";

import { BackLink } from "@/components/ui/BackLink";
import { AcquisitionPanel } from "@/components/facility/AcquisitionPanel";
import { SupplementalUpload } from "@/components/facility/SupplementalUpload";
import { api } from "@/lib/api";
import type { ModelStatusResponse } from "@/types";


export default async function FacilityDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const data = await api.getFacility(id);

  const unitStatuses = await Promise.all(
    data.units.map(async (unit) => {
      try {
        const status = await api.getModelStatus(unit.unit_id);
        return { unitId: unit.unit_id, status };
      } catch {
        return { unitId: unit.unit_id, status: null };
      }
    })
  );
  const statusByUnit = Object.fromEntries(
    unitStatuses.map(({ unitId, status }) => [unitId, status])
  ) as Record<string, ModelStatusResponse | null>;

  return (
    <main className="shell">
      <BackLink href="/dashboard" label="Hub" />
      <div className="panel">
        <div className="eyebrow">{data.facility.address}</div>
        <h1 className="page-title">{data.facility.name}</h1>
        <p className="muted">
          Live safety analysis, 3D world model inspection, scenario simulation, and compliance reports.
        </p>
      </div>
      <div style={{ height: 20 }} />
      <SupplementalUpload facilityId={id} />
      <div style={{ height: 20 }} />
      <div className="card-grid">
        {data.units.map((unit) => (
          <div key={unit.unit_id} style={{ display: "grid", gap: 16 }}>
            <div className="feed-card">
              <div className="eyebrow">Floor {unit.floor} · {unit.unit_type}</div>
              <h3 style={{ margin: "6px 0 16px" }}>{unit.name}</h3>
              <AcquisitionPanel
                facilityId={id}
                unitId={unit.unit_id}
                initialStatus={statusByUnit[unit.unit_id] ?? null}
              />
            </div>
            <div className="cta-row">
              <Link className="button" href={`/facility/${id}/model/${unit.unit_id}` as Route}>
                Open model
              </Link>
              <Link className="button secondary" href={`/facility/${id}/simulation/${unit.unit_id}` as Route}>
                Simulate crisis
              </Link>
              <Link className="button secondary" href={`/facility/${id}/report/${unit.unit_id}` as Route}>
                Report
              </Link>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
