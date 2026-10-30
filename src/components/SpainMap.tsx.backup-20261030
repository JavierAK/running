import { useEffect, useMemo, useState } from 'react';
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
  geometry: {
    type: 'Polygon' | 'MultiPolygon';
    coordinates: number[][][][];
  };
};

type GeoData = {
  type: 'FeatureCollection';
  features: GeoFeature[];
};

const BOUNDS = { minLng: -9.5, maxLng: 4.5, minLat: 35.5, maxLat: 44.2 };

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
      .map((ring) => ringToPath(ring as unknown as number[][], w, h))
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
  const [visitedProvinces, setVisitedProvinces] = useState<Set<string>>(
    new Set()
  );
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);

  useEffect(() => {
    // Fetch Map GeoJSON and lean Visited Provinces JSON in parallel
    Promise.all([
      fetch(`${import.meta.env.BASE_URL}static/spain-provinces.geojson`).then(
        (res) => res.json()
      ),
      fetch(`${import.meta.env.BASE_URL}visited-provinces.json`)
        .then((res) => res.json())
        .catch(() => ({ visited: [] })),
    ])
      .then(([geoJsonData, visitedData]) => {
        setGeoData(geoJsonData);
        setVisitedProvinces(new Set(visitedData.visited || []));
      })
      .catch((err) => console.error('Failed to load map static assets:', err));
  }, []);

  // Compute local activity counts if activity details exist in memory
  const provinceCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    const safeActivities = activities || [];
    const filtered =
      filter === 'all'
        ? safeActivities
        : safeActivities.filter((a) => a && a.type === filter);

    for (const act of filtered) {
      if (!act) continue;
      const prov = extractProvince(act.location_country);
      if (prov) {
        counts[prov] = (counts[prov] || 0) + 1;
      }
    }
    return counts;
  }, [activities, filter]);

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

            // Checked against the visited JSON set OR dynamic activity counts
            const visited =
              visitedProvinces.has(name) || (provinceCounts[name] || 0) > 0;
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
