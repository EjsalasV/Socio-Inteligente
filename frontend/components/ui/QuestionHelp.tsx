"use client";

type QuestionHelpProps = {
  text?: string;
};

export default function QuestionHelp({ text }: QuestionHelpProps) {
  if (!text) return null;

  return (
    <span className="relative inline-flex items-center group">
      <button
        type="button"
        aria-label={text}
        className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-[#041627]/20 bg-white text-[10px] font-bold text-[#041627] leading-none shadow-sm"
      >
        ?
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 w-56 -translate-x-1/2 rounded-xl border border-[#041627]/10 bg-[#041627] px-3 py-2 text-[11px] leading-snug text-white shadow-lg opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100"
      >
        {text}
      </span>
    </span>
  );
}
