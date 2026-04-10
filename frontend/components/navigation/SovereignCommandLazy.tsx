"use client";

import dynamic from "next/dynamic";

const SovereignCommand = dynamic(() => import("./SovereignCommand"), {
  ssr: false,
});

export default function SovereignCommandLazy() {
  return <SovereignCommand />;
}
