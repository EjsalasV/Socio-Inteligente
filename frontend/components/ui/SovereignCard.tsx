import { formatMoney, moneyClass } from "../../lib/formatters";

type Props = {
  title: string;
  value: string | number;
  subtext?: string;
  type?: "default" | "error";
};

export default function SovereignCard({ title, value, subtext, type = "default" }: Props) {
  const borderClass =
    type === "error"
      ? "border-l-4 border-editorial-error"
      : "border border-ghost";
  const renderedValue = typeof value === "number" ? formatMoney(value) : value;
  const valueClass = moneyClass(value);

  return (
    <div
      className={`bg-white p-6 rounded-editorial shadow-editorial ${borderClass} transition-all duration-200 hover:-translate-y-[2px] hover:shadow-[0_18px_36px_rgba(24,28,30,0.09)]`}
    >
      <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-400 font-body">{title}</h3>
      <p className={`text-2xl font-bold mt-2 font-body ${valueClass}`}>{renderedValue}</p>
      {subtext ? <p className="text-sm text-slate-500 mt-1 italic font-headline">{subtext}</p> : null}
    </div>
  );
}
