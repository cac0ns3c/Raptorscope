// SPDX-License-Identifier: GPL-3.0-or-later
// Inline stroke icons (currentColor), no external assets — CSP/offline safe.
import type { SVGProps } from "react";

function Svg(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    />
  );
}

export const IconLogo = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <path d="M12 2 4 5v6c0 5 3.4 8.2 8 11 4.6-2.8 8-6 8-11V5l-8-3Z" />
    <path d="M9.2 12.2 11 14l4-4.2" />
  </Svg>
);

export const IconGauge = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <path d="M12 13a3 3 0 0 0 3-3" />
    <circle cx="12" cy="12" r="9" />
    <path d="M12 12 8.5 8.5" />
  </Svg>
);

export const IconLayers = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <path d="m12 3 9 5-9 5-9-5 9-5Z" />
    <path d="m3 13 9 5 9-5" />
  </Svg>
);

export const IconClock = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </Svg>
);

export const IconBell = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.7 21a2 2 0 0 1-3.4 0" />
  </Svg>
);

export const IconHost = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <rect x="3" y="4" width="18" height="12" rx="2" />
    <path d="M8 20h8M12 16v4" />
  </Svg>
);

export const IconChevronRight = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <path d="m9 6 6 6-6 6" />
  </Svg>
);

export const IconAlert = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <path d="M12 3 2 20h20L12 3Z" />
    <path d="M12 10v4M12 17h.01" />
  </Svg>
);

export const IconSearch = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.2-3.2" />
  </Svg>
);

export const IconShieldCheck = (p: SVGProps<SVGSVGElement>) => (
  <Svg {...p}>
    <path d="M12 3 5 6v5c0 4 2.6 6.6 7 8 4.4-1.4 7-4 7-8V6l-7-3Z" />
    <path d="m9 12 2 2 4-4" />
  </Svg>
);
