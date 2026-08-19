import Link from "next/link";

export default function AlphaBanner() {
  return (
    <div className="relative z-[60] border-b border-amber-300 bg-[#fff3c4] px-4 py-2 text-center text-xs font-semibold text-[#6b4300]">
      <span className="mr-2 rounded-full bg-[#6b4300] px-2 py-0.5 text-[10px] uppercase tracking-[0.14em] text-white">Alpha cerrada</span>
      SocioAI no es un producto final. Usa datos ficticios o anonimizados y valida toda recomendación con tu juicio profesional.{" "}
      <Link href="/legal/privacidad" className="underline underline-offset-2">Privacidad y límites</Link>
    </div>
  );
}
