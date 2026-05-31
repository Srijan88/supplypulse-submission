"use client";

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleDot,
  Database,
  Info,
  MapPinned,
  PackageSearch,
  Radar,
  Route,
  Ship,
  Sparkles,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  APIProvider,
  Map as GoogleMap,
  Marker,
  useMap,
} from "@vis.gl/react-google-maps";
import type { EquipmentItem, PipelineResult } from "@/lib/types";

type LatLng = {
  lat: number;
  lng: number;
};

type CountryPoint = {
  country: string;
  position: LatLng;
};

type MapRoute = {
  id: string;
  itemCode: string;
  itemName: string;
  sourceCountry: string;
  destinationCountry: string;
  sourcePosition: LatLng;
  destinationPosition: LatLng;
  plannedNeedDate?: string;
  forecastArrival?: string;
  delayDays: number;
  scheduleExposure: number;
  statusBand: string;
  geoExposure: string;
  tradeExposure: string;
  routeExposure: string;
  geoReason?: string;
  tradeReason?: string;
  routeReason?: string;
};

const googleMapsApiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "";

const countryCoordinates: Record<string, LatLng> = {
  Taiwan: { lat: 23.6978, lng: 120.9605 },
  Singapore: { lat: 1.3521, lng: 103.8198 },
  Switzerland: { lat: 46.8182, lng: 8.2275 },
  "United States": { lat: 39.8283, lng: -98.5795 },
  Japan: { lat: 36.2048, lng: 138.2529 },
  Netherlands: { lat: 52.1326, lng: 5.2913 },
  Denmark: { lat: 56.2639, lng: 9.5018 },
  Australia: { lat: -25.2744, lng: 133.7751 },
  Sweden: { lat: 60.1282, lng: 18.6435 },
  Brazil: { lat: -14.235, lng: -51.9253 },
  China: { lat: 35.8617, lng: 104.1954 },
  India: { lat: 20.5937, lng: 78.9629 },
  Malaysia: { lat: 4.2105, lng: 101.9758 },
  "United Arab Emirates": { lat: 23.4241, lng: 53.8478 },
  Germany: { lat: 51.1657, lng: 10.4515 },
  Italy: { lat: 41.8719, lng: 12.5674 },
  "South Korea": { lat: 35.9078, lng: 127.7669 },
  France: { lat: 46.2276, lng: 2.2137 },
};

const cleanMapStyles: google.maps.MapTypeStyle[] = [
  {
    featureType: "poi",
    stylers: [{ visibility: "off" }],
  },
  {
    featureType: "transit",
    stylers: [{ visibility: "off" }],
  },
  {
    featureType: "road",
    elementType: "labels.icon",
    stylers: [{ visibility: "off" }],
  },
  {
    featureType: "administrative.country",
    elementType: "geometry.stroke",
    stylers: [{ color: "#94a3b8" }, { weight: 1 }],
  },
  {
    featureType: "water",
    elementType: "geometry.fill",
    stylers: [{ color: "#dbeafe" }],
  },
  {
    featureType: "landscape",
    elementType: "geometry.fill",
    stylers: [{ color: "#f8fafc" }],
  },
];

export function SupplyMap({ result }: { result: PipelineResult }) {
  const [selectedRoute, setSelectedRoute] = useState<MapRoute | null>(null);

  const routes = useMemo(() => buildMapRoutes(result), [result]);
  const countries = useMemo(() => buildCountryPoints(routes), [routes]);

  const highRoutes = routes.filter((route) =>
    route.statusBand.toLowerCase().includes("high")
  );

  const evidenceSearchCount =
    result.pipelineAudit?.evidenceSearchSummary?.filter(
      (event) => event.eventType === "search_request"
    ).length ?? 0;

  const activeExternalExposureCount = [
    result.geoResult,
    result.tradeResult,
    result.routeResult,
  ].filter(Boolean).length;

  if (!googleMapsApiKey) {
    return <MissingKeyState />;
  }

  return (
    <div className="space-y-5">
      <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 bg-gradient-to-r from-white via-violet-50/70 to-indigo-50/70 p-5">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-black text-violet-700 shadow-sm ring-1 ring-violet-100">
                <MapPinned size={14} />
                Supply Exposure Map
              </div>

              <h2 className="mt-3 text-2xl font-black tracking-tight text-slate-950">
                Route-aware delivery exposure view
              </h2>

              <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
                Explore source countries, destination countries, high-exposure
                delivery routes, and item-level external exposure signals.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 xl:w-[620px]">
              <MapMetric
                label="Mapped Routes"
                value={routes.length}
                icon={<Route size={17} />}
              />
              <MapMetric
                label="High Status"
                value={highRoutes.length}
                icon={<AlertTriangle size={17} />}
                tone="danger"
              />
              <MapMetric
                label="Analyses"
                value={activeExternalExposureCount}
                icon={<Radar size={17} />}
                tone="violet"
              />
              <MapMetric
                label="Evidence Searches"
                value={evidenceSearchCount}
                icon={<Database size={17} />}
                tone="success"
              />
            </div>
          </div>
        </div>

        <div className="grid xl:grid-cols-[minmax(0,1fr)_400px]">
          <div className="relative h-[660px] bg-slate-100">
            <APIProvider apiKey={googleMapsApiKey}>
              <GoogleMap
                defaultCenter={{ lat: 20, lng: 80 }}
                defaultZoom={3}
                gestureHandling="greedy"
                disableDefaultUI={true}
                zoomControl={true}
                fullscreenControl={true}
                mapTypeControl={false}
                streetViewControl={false}
                styles={cleanMapStyles}
                style={{
                  width: "100%",
                  height: "660px",
                }}
              >
                <FitBoundsLayer routes={routes} />

                <RoutePolylineLayer
                  routes={routes}
                  selectedRoute={selectedRoute}
                  onSelectRoute={setSelectedRoute}
                />

                {countries.map((point) => {
                  const relatedRoutes = routes.filter(
                    (route) =>
                      route.sourceCountry === point.country ||
                      route.destinationCountry === point.country
                  );

                  const relatedRoute = relatedRoutes[0];

                  const highestExposureForCountry = Math.max(
                    ...relatedRoutes.map((route) => route.scheduleExposure),
                    0
                  );

                  const color =
                    highestExposureForCountry >= 100
                      ? "#ef4444"
                      : highestExposureForCountry > 0
                        ? "#7c3aed"
                        : "#10b981";

                  return (
                    <Marker
                      key={point.country}
                      position={point.position}
                      title={point.country}
                      label={{
                        text: point.country,
                        color: "#111827",
                        fontWeight: "800",
                        fontSize: "12px",
                      }}
                      icon={createMarkerIcon(color)}
                      onClick={() => {
                        if (relatedRoute) {
                          setSelectedRoute(relatedRoute);
                        }
                      }}
                    />
                  );
                })}
              </GoogleMap>
            </APIProvider>

            <div className="absolute left-5 top-5 max-w-sm rounded-3xl border border-slate-200 bg-white/95 p-4 shadow-xl backdrop-blur">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-violet-50 p-2 text-violet-700">
                  <Sparkles size={17} />
                </div>
                <div>
                  <div className="text-sm font-black text-slate-950">
                    SupplyPulse route layer
                  </div>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Click a route card or marker to inspect schedule exposure,
                    affected item, and external exposure evidence.
                  </p>
                </div>
              </div>
            </div>

            <div className="absolute bottom-5 left-5 rounded-3xl border border-slate-200 bg-white/95 p-4 shadow-xl backdrop-blur">
              <div className="text-xs font-black uppercase tracking-wide text-slate-500">
                Status Band Legend
              </div>
              <div className="mt-3 grid gap-2 text-xs font-semibold text-slate-700">
                <LegendItem color="#ef4444" label="High status band" />
                <LegendItem color="#f59e0b" label="Medium status band" />
                <LegendItem color="#3b82f6" label="Low status band" />
                <LegendItem color="#10b981" label="On track" />
              </div>
            </div>
          </div>

          <aside className="h-[660px] overflow-auto border-t border-slate-200 bg-white xl:border-l xl:border-t-0">
            {selectedRoute ? (
              <RouteDetailPanel
                route={selectedRoute}
                onClose={() => setSelectedRoute(null)}
              />
            ) : (
              <RouteListPanel
                routes={routes}
                onSelectRoute={setSelectedRoute}
              />
            )}
          </aside>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <ExposureSummaryCard
          title="Geopolitical Exposure"
          level={result.geoResult?.geoExposureLevel || "Not Run"}
          summary={
            result.geoResult?.geoExposureSummary ||
            "Run a geopolitical exposure analysis to populate this card."
          }
        />
        <ExposureSummaryCard
          title="Trade / Tariff Exposure"
          level={result.tradeResult?.tradeExposureLevel || "Not Run"}
          summary={
            result.tradeResult?.tradeExposureSummary ||
            "Run a trade / tariff exposure analysis to populate this card."
          }
        />
        <ExposureSummaryCard
          title="Route / Logistics Exposure"
          level={result.routeResult?.routeExposureLevel || "Not Run"}
          summary={
            result.routeResult?.routeExposureSummary ||
            "Run a route / logistics exposure analysis to populate this card."
          }
        />
      </section>
    </div>
  );
}

function FitBoundsLayer({ routes }: { routes: MapRoute[] }) {
  const map = useMap();

  useEffect(() => {
    if (!map || !window.google?.maps || routes.length === 0) {
      return;
    }

    const bounds = new window.google.maps.LatLngBounds();

    routes.forEach((route) => {
      bounds.extend(route.sourcePosition);
      bounds.extend(route.destinationPosition);
    });

    window.setTimeout(() => {
      map.fitBounds(bounds, 90);
    }, 250);
  }, [map, routes]);

  return null;
}

function RoutePolylineLayer({
  routes,
  selectedRoute,
  onSelectRoute,
}: {
  routes: MapRoute[];
  selectedRoute: MapRoute | null;
  onSelectRoute: (route: MapRoute) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map || !window.google?.maps) {
      return;
    }

    const polylines = routes.map((route) => {
      const selected = selectedRoute?.id === route.id;

      const polyline = new window.google.maps.Polyline({
        path: [route.sourcePosition, route.destinationPosition],
        geodesic: true,
        strokeColor: getRouteColor(route),
        strokeOpacity: selected ? 1 : 0.78,
        strokeWeight: selected
          ? getRouteStrokeWidth(route) + 2
          : getRouteStrokeWidth(route),
        clickable: true,
        map,
      });

      polyline.addListener("click", () => {
        onSelectRoute(route);
      });

      return polyline;
    });

    return () => {
      polylines.forEach((polyline) => {
        polyline.setMap(null);
      });
    };
  }, [map, routes, selectedRoute, onSelectRoute]);

  return null;
}

function MissingKeyState() {
  return (
    <div className="supply-card p-8">
      <div className="mx-auto max-w-2xl text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-3xl bg-amber-50 text-amber-700">
          <AlertTriangle size={24} />
        </div>

        <h2 className="mt-4 text-2xl font-black text-slate-950">
          Google Maps API key missing
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          Add your key to <code>.env.local</code> and restart the frontend.
        </p>

        <pre className="mt-5 overflow-auto rounded-2xl bg-slate-950 p-4 text-left text-sm text-slate-100">
{`NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_key_here
NEXT_PUBLIC_SUPPLYPULSE_API_BASE=http://127.0.0.1:8000`}
        </pre>
      </div>
    </div>
  );
}

function buildMapRoutes(result: PipelineResult): MapRoute[] {
  const items = result.scheduleResult?.equipmentItems || [];

  const geoAffected = new globalThis.Map(
    (result.geoResult?.affectedItems || []).map((item) => [
      item.equipmentCode,
      item,
    ])
  );

  const tradeAffected = new globalThis.Map(
    (result.tradeResult?.affectedItems || []).map((item) => [
      item.equipmentCode,
      item,
    ])
  );

  const routeAffected = new globalThis.Map(
    (result.routeResult?.affectedItems || []).map((item) => [
      item.equipmentCode,
      item,
    ])
  );

  return items
    .map((item: EquipmentItem): MapRoute | null => {
      const sourceCountry = item.originCountry || "";
      const destinationCountry = item.projectCountry || "";

      const sourcePosition = countryCoordinates[sourceCountry];
      const destinationPosition = countryCoordinates[destinationCountry];

      if (!sourcePosition || !destinationPosition) {
        return null;
      }

      const geoItem = geoAffected.get(item.equipmentCode);
      const tradeItem = tradeAffected.get(item.equipmentCode);
      const routeItem = routeAffected.get(item.equipmentCode);

      return {
        id: `${item.equipmentCode}-${sourceCountry}-${destinationCountry}`,
        itemCode: item.equipmentCode || "Unknown",
        itemName: item.equipmentName || "Unknown item",
        sourceCountry,
        destinationCountry,
        sourcePosition,
        destinationPosition,
        plannedNeedDate: item.baselineDueDate,
        forecastArrival: item.latestExpectedDeliveryDate,
        delayDays: Number(item.delayDays || 0),
        scheduleExposure: Number(item.scheduleRiskPercentage || 0),
        statusBand: item.scheduleRiskLevel || "Unknown",
        geoExposure: geoItem
          ? result.geoResult?.geoExposureLevel || "Assessed"
          : "Not assessed",
        tradeExposure: tradeItem
          ? result.tradeResult?.tradeExposureLevel || "Assessed"
          : "Not assessed",
        routeExposure: routeItem
          ? result.routeResult?.routeExposureLevel || "Assessed"
          : "Not assessed",
        geoReason: geoItem?.geoExposureReason,
        tradeReason: tradeItem?.tradeExposureReason,
        routeReason: routeItem?.routeExposureReason,
      };
    })
    .filter(Boolean) as MapRoute[];
}

function buildCountryPoints(routes: MapRoute[]): CountryPoint[] {
  const points = new globalThis.Map<string, CountryPoint>();

  routes.forEach((route) => {
    points.set(route.sourceCountry, {
      country: route.sourceCountry,
      position: route.sourcePosition,
    });

    points.set(route.destinationCountry, {
      country: route.destinationCountry,
      position: route.destinationPosition,
    });
  });

  return Array.from(points.values());
}

function createMarkerIcon(color: string) {
  if (!window.google?.maps) {
    return undefined;
  }

  const svg = `
    <svg width="34" height="34" viewBox="0 0 34 34" xmlns="http://www.w3.org/2000/svg">
      <circle cx="17" cy="17" r="13" fill="${color}" stroke="white" stroke-width="4"/>
      <circle cx="17" cy="17" r="5" fill="white" opacity="0.95"/>
    </svg>
  `;

  return {
    url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`,
    scaledSize: new window.google.maps.Size(34, 34),
    anchor: new window.google.maps.Point(17, 17),
    labelOrigin: new window.google.maps.Point(17, -8),
  };
}

function getRouteColor(route: MapRoute) {
  const status = route.statusBand.toLowerCase();

  if (status.includes("high")) {
    return "#ef4444";
  }

  if (status.includes("medium")) {
    return "#f59e0b";
  }

  if (status.includes("low")) {
    return "#3b82f6";
  }

  if (status.includes("track")) {
    return "#10b981";
  }

  return "#7c3aed";
}

function getRouteStrokeWidth(route: MapRoute) {
  if (route.scheduleExposure >= 100) {
    return 5;
  }

  if (route.scheduleExposure >= 50) {
    return 4;
  }

  if (route.scheduleExposure > 0) {
    return 3;
  }

  return 2;
}

function MapMetric({
  label,
  value,
  icon,
  tone = "default",
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  tone?: "default" | "danger" | "success" | "violet";
}) {
  const toneClass =
    tone === "danger"
      ? "bg-rose-50 text-rose-700"
      : tone === "success"
        ? "bg-emerald-50 text-emerald-700"
        : tone === "violet"
          ? "bg-violet-50 text-violet-700"
          : "bg-slate-50 text-slate-700";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className={`mb-2 inline-flex rounded-xl p-2 ${toneClass}`}>
        {icon}
      </div>
      <div className="text-xl font-black text-slate-950">{value}</div>
      <div className="mt-1 text-[10px] font-black uppercase tracking-wide text-slate-500">
        {label}
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="h-2.5 w-8 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span>{label}</span>
    </div>
  );
}

function RouteListPanel({
  routes,
  onSelectRoute,
}: {
  routes: MapRoute[];
  onSelectRoute: (route: MapRoute) => void;
}) {
  const sortedRoutes = [...routes].sort(
    (a, b) => b.scheduleExposure - a.scheduleExposure
  );

  return (
    <div className="p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-2xl bg-violet-50 p-2 text-violet-700">
          <PackageSearch size={18} />
        </div>
        <div>
          <h3 className="text-lg font-black text-slate-950">Mapped Items</h3>
          <p className="text-xs text-slate-500">
            Sorted by Schedule Exposure %
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {sortedRoutes.map((route) => (
          <button
            key={route.id}
            onClick={() => onSelectRoute(route)}
            className="group w-full rounded-3xl border border-slate-200 bg-white p-4 text-left transition hover:border-violet-200 hover:bg-violet-50 hover:shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-black text-slate-950">
                  {route.itemCode}
                </div>
                <div className="mt-1 text-xs leading-5 text-slate-500">
                  {route.itemName}
                </div>
              </div>

              <StatusPill status={route.statusBand} />
            </div>

            <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-slate-600">
              <span>{route.sourceCountry}</span>
              <ArrowRight size={14} className="text-violet-600" />
              <span>{route.destinationCountry}</span>
            </div>

            <div className="mt-3 text-sm font-black text-slate-950">
              {route.scheduleExposure.toFixed(2)}% Schedule Exposure
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function RouteDetailPanel({
  route,
  onClose,
}: {
  route: MapRoute;
  onClose: () => void;
}) {
  return (
    <div className="p-5">
      <div className="mb-5 flex items-center justify-between gap-3">
        <button
          onClick={onClose}
          className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-200"
        >
          Back to routes
        </button>

        <button
          onClick={onClose}
          className="rounded-full bg-white p-2 text-slate-400 ring-1 ring-slate-200 hover:text-slate-700"
          aria-label="Close route detail"
        >
          <X size={16} />
        </button>
      </div>

      <div className="flex items-start gap-3">
        <div className="rounded-2xl bg-violet-50 p-3 text-violet-700">
          <Ship size={20} />
        </div>
        <div>
          <div className="text-xs font-black uppercase tracking-wide text-violet-700">
            {route.itemCode}
          </div>
          <h3 className="mt-1 text-xl font-black leading-tight text-slate-950">
            {route.itemName}
          </h3>
          <p className="mt-2 text-sm text-slate-500">
            {route.sourceCountry} → {route.destinationCountry}
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <DetailMetric
          label="Schedule Exposure"
          value={`${route.scheduleExposure.toFixed(2)}%`}
        />
        <DetailMetric label="Delay / Gain" value={`${route.delayDays} days`} />
        <DetailMetric
          label="Planned Need"
          value={route.plannedNeedDate || "—"}
        />
        <DetailMetric
          label="Forecast Arrival"
          value={route.forecastArrival || "—"}
        />
      </div>

      <div className="mt-5 rounded-3xl border border-slate-200 bg-slate-50 p-4">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">
          External Exposure
        </div>

        <div className="mt-4 grid gap-3">
          <ExposureLine
            title="Geopolitical"
            value={route.geoExposure}
            reason={route.geoReason}
          />
          <ExposureLine
            title="Trade / Tariff"
            value={route.tradeExposure}
            reason={route.tradeReason}
          />
          <ExposureLine
            title="Route / Logistics"
            value={route.routeExposure}
            reason={route.routeReason}
          />
        </div>
      </div>

      <div className="mt-5 rounded-3xl bg-violet-50 p-4 text-sm leading-6 text-violet-900 ring-1 ring-violet-100">
        <strong>SupplyPulse note:</strong> Schedule Exposure % is a
        delay-pressure index, not a probability.
      </div>
    </div>
  );
}

function DetailMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
      <div className="text-[10px] font-black uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="mt-1 text-sm font-black text-slate-950">{value}</div>
    </div>
  );
}

function ExposureLine({
  title,
  value,
  reason,
}: {
  title: string;
  value: string;
  reason?: string;
}) {
  const assessed = value !== "Not assessed";

  return (
    <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-black text-slate-950">{title}</div>
        <span
          className={[
            "rounded-full px-2.5 py-1 text-xs font-bold",
            assessed
              ? "bg-violet-50 text-violet-700 ring-1 ring-violet-100"
              : "bg-slate-100 text-slate-500 ring-1 ring-slate-200",
          ].join(" ")}
        >
          {value}
        </span>
      </div>

      {reason ? (
        <p className="mt-2 text-xs leading-5 text-slate-500">{reason}</p>
      ) : (
        <p className="mt-2 text-xs leading-5 text-slate-400">
          No item-specific evidence was linked for this exposure type.
        </p>
      )}
    </div>
  );
}

function ExposureSummaryCard({
  title,
  level,
  summary,
}: {
  title: string;
  level: string;
  summary: string;
}) {
  return (
    <div className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-black text-slate-950">{title}</h3>
          <p className="mt-2 line-clamp-5 text-sm leading-6 text-slate-500">
            {summary}
          </p>
        </div>
        <StatusPill status={level} />
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const lowered = status.toLowerCase();

  const className = lowered.includes("high")
    ? "bg-rose-50 text-rose-700 ring-rose-200"
    : lowered.includes("medium")
      ? "bg-amber-50 text-amber-700 ring-amber-200"
      : lowered.includes("low")
        ? "bg-blue-50 text-blue-700 ring-blue-200"
        : lowered.includes("track")
          ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
          : "bg-slate-100 text-slate-600 ring-slate-200";

  const Icon = lowered.includes("track") ? CheckCircle2 : CircleDot;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${className}`}
    >
      <Icon size={12} />
      {status}
    </span>
  );
}