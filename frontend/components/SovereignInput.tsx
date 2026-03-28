import type { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement>;

export default function SovereignInput(props: Props) {
  return <input {...props} className={`ghost-input w-full ${props.className ?? ""}`} />;
}
