import { useEffect, useMemo, useState } from 'react';
import * as polyline from '@mapbox/polyline';
import type { Activity, SportFilter } from '../types';
import { useLocale } from '../hooks/useLocale';
import { extractProvince } from '../hooks/useActivities';

interface SpainMapProps {
  activities?: Activity[];
  filter?: SportFilter;
  onSelectProvince?: (province: string | null) => void;
  selectedProvince?: string | null;
}

type GeoFeature = {
  type: 'Feature';
  properties: { name: string };
  geometry:
    | { type: 'Polygon'; coordinates: number[][][] }
    | { type: 'MultiPolygon'; coordinates: number[][][][] };
};

type GeoData = {
  type: 'FeatureCollection';
  features: GeoFeature[];
};

type ProvincePolygon = {
  rings: number[][][];
  minLng: number;
  maxLng: number;
  minLat: number;
  maxLat: number;
};

type PreparedProvince = {
  name: string;
  polygons: ProvincePolygon[];
};

const BOUNDS = { minLng: -9.5, maxLng: 4.5, minLat: 35.5, maxLat: 44.2 };

function prepareProvince(feature: GeoFeature): PreparedProvince {
  const polygons =
    feature.geometry.type === 'Polygon'
      ? [feature.geometry.coordinates]
      : feature.geometry.coordinates;

  return {
    name: feature.properties.name,
    polygons: polygons.map((rings) => {
      const outerRing = rings[0] || [];
      const longitudes = outerRing.map((point) => point[0]);
      const latitudes = outerRing.map((point) => point[1]);

      return {
        rings,
        minLng: Math.min(...longitudes),
        maxLng: Math.max(...longitudes),
        minLat: Math.min(...latitudes),
        maxLat: Math.max(...latitudes),
      };
    }),
  };
}

function pointInRing(
  lng: number,
  lat: number,
  ring: number[][]
): boolean {
  let inside = false;

  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];

    const intersects =
      (yi > lat) !== (yj > lat) &&
      lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi;

    if (intersects) inside = !inside;
  }

  return inside;
}

function pointInPolygon(
  lng: number,
  lat: number,
  polygon: ProvincePolygon
): boolean {
  if (
    lng < polygon.minLng ||
    lng > polygon.maxLng ||
    lat < polygon.minLat ||
    lat > polygon.maxLat
  ) {
    return false;
  }

  const outerRing = polygon.rings[0];
  if (!outerRing || !pointInRing(lng, lat, outerRing)) return false;

  // Exclude holes inside the polygon.
  for (const hole of polygon.rings.slice(1)) {
    if (pointInRing(lng, lat, hole)) return false;
  }

  return true;
}

function findProvince(
  lng: number,
  lat: number,
  provinces: PreparedProvince[]
): string | null {
  for (const province of provinces) {
    if (
      province.polygons.some((polygon) =>
        pointInPolygon(lng, lat, polygon)
      )
    ) {
      return province.name;
    }
  }

  return null;
}

function project(
  lng: number,
  lat: number,
  w: number,
  h: number
): [number, number] {
  const x = ((lng - BOUNDS.minLng) / (BOUNDS.maxLng - BOUNDS.minLng)) * w;
  const y = h - ((lat - BOUNDS.minLat) / (BOUNDS.maxLat - BOUNDS.minLat)) * h;
  return [x, y];
}

function ringToPath(ring: number[][], w: number, h: number): string {
  return (
    ring
      .map(([lng, lat], i) => {
        const [x, y] = project(lng, lat, w, h);
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ') + ' Z'
  );
}

function featureToPath(feature: GeoFeature, w: number, h: number): string {
  const geom = feature.geometry;
  if (!geom) return '';

  if (geom.type === 'Polygon') {
    return geom.coordinates
      .map((ring) => ringToPath(ring, w, h))
      .join(' ');
  }

  if (geom.type === 'MultiPolygon') {
    return geom.coordinates
      .map((poly) => poly.map((ring) => ringToPath(ring, w, h)).join(' '))
      .join(' ');
  }

  return '';
}

export function SpainMap({
  activities = [],
  filter = 'all',
  onSelectProvince,
  selectedProvince,
}: SpainMapProps) {
  const { locale } = useLocale();
  const [geoData, setGeoData] = useState<GeoData | null>(null);
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}static/spain-provinces.geojson`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`GeoJSON request failed: ${res.status}`);
        }
        return res.json() as Promise<GeoData>;
      })
      .then((geoJsonData) => {
        setGeoData(geoJsonData);
      })
      .catch((err) => console.error('Failed to load map static assets:', err));
  }, []);

  const preparedProvinces = useMemo(
    () => geoData?.features.map(prepareProvince) || [],
    [geoData]
  );

  // Detect provinces from real GPS routes, with location text as fallback.
  const provinceCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    const safeActivities = activities || [];

    const filtered =
      filter === 'all'
        ? safeActivities
        : safeActivities.filter((a) => a && a.type === filter);

    for (const act of filtered) {
      if (!act) continue;

      // Indoor/treadmill routes may have borrowed GPS paths.
      const subtype = String(act.subtype || '').toLowerCase();
      if (subtype === 'indoor' || subtype === 'treadmill') continue;

      const provincesForActivity = new Set<string>();
      const encodedRoute = act.summary_polyline;

      if (encodedRoute && preparedProvinces.length > 0) {
        try {
          // polyline.decode returns [latitude, longitude].
          const points = polyline.decode(encodedRoute);

          for (const [lat, lng] of points) {
            if (
              !Number.isFinite(lat) ||
              !Number.isFinite(lng) ||
              lng < BOUNDS.minLng ||
              lng > BOUNDS.maxLng ||
              lat < BOUNDS.minLat ||
              lat > BOUNDS.maxLat
            ) {
              continue;
            }

            const province = findProvince(lng, lat, preparedProvinces);
            if (province) provincesForActivity.add(province);
          }
        } catch {
          // Invalid polylines fall back to the location text.
        }
      }

      // Use reverse-geocoded location only if GPS did not identify a province.
      if (provincesForActivity.size === 0) {
        const province = extractProvince(act.location_country);
        if (province) provincesForActivity.add(province);
      }

      // Count an activity once per province.
      for (const province of provincesForActivity) {
        counts[province] = (counts[province] || 0) + 1;
      }
    }

    return counts;
  }, [activities, filter, preparedProvinces]);

  const SVG_W = 400;
  const SVG_H = 220;

  const displayProvince = hoveredProvince || selectedProvince;
  const displayCount = displayProvince
    ? provinceCounts[displayProvince] || 0
    : 0;

  const activityLabel = locale === 'zh' ? '次活动' : 'activities';
  const filteredLabel = locale === 'zh' ? '（已筛选）' : '(filtered)';

  const handleClick = (name: string) => {
    if (!onSelectProvince) return;

    if (selectedProvince === name) {
      onSelectProvince(null);
    } else {
      onSelectProvince(name);
    }
  };

  if (!geoData || !geoData.features) {
    return (
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 text-center text-xs text-[var(--color-muted)]">
        Loading map...
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 transition-all duration-300 hover:border-[var(--color-accent)]/30 hover:shadow-lg">
      <div className="flex items-center justify-between pb-2">
        <span className="text-xs font-semibold tracking-wider text-[var(--color-muted)] uppercase">
          {locale === 'zh' ? '巴拿马地图' : 'Mapa de España'}
        </span>
        {selectedProvince && (
          <button
            type="button"
            onClick={() => onSelectProvince?.(null)}
            className="text-xs text-[var(--color-accent)] hover:underline"
          >
            {locale === 'zh' ? '清除筛选' : 'Clear filter'}
          </button>
        )}
      </div>

      <div className="relative aspect-[400/220] w-full">
        <svg
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          className="h-full w-full"
          style={{ overflow: 'visible' }}
        >
          {geoData.features.map((feature) => {
            const name = feature.properties?.name;
            if (!name) return null;

            const visited = (provinceCounts[name] || 0) > 0;
            const isSelected = selectedProvince === name;
            const isHovered = hoveredProvince === name;

            let fill = 'var(--color-border)';

            if (visited) {
              if (isSelected || isHovered) {
                fill = 'var(--color-accent)';
              } else {
                fill =
                  'color-mix(in srgb, var(--color-accent) 55%, transparent)';
              }
            } else if (isHovered) {
              fill = 'var(--color-accent)/30';
            }

            return (
              <path
                key={name}
                d={featureToPath(feature, SVG_W, SVG_H)}
                fill={fill}
                stroke="var(--color-bg)"
                strokeWidth="0.5"
                className={`transition-all duration-150 ${
                  visited ? 'cursor-pointer' : 'cursor-default'
                }`}
                onMouseEnter={() => setHoveredProvince(name)}
                onMouseLeave={() => setHoveredProvince(null)}
                onClick={() => visited && handleClick(name)}
              />
            );
          })}
        </svg>
      </div>

      {/* Tooltip */}
      <div className="mt-1.5 h-4 text-xs text-[var(--color-muted)]">
        {displayProvince && (
          <>
            <span className="font-medium text-[var(--color-text)]">
              {displayProvince}
            </span>
            {displayCount > 0 && (
              <span className="ml-1.5">
                {displayCount} {activityLabel}
              </span>
            )}
            {selectedProvince === displayProvince && !hoveredProvince && (
              <span className="ml-1.5 text-[var(--color-accent)]">
                {filteredLabel}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
}
