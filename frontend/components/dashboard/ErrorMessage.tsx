type Props = {
  message: string;
};

export default function ErrorMessage({ message }: Props) {
  return (
    <section className="sovereign-card border-l-4 border-editorial-error">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500 font-body">Error de carga</p>
      <h2 className="font-headline text-3xl text-navy-900 mt-2">No se pudo abrir el módulo</h2>
      <p className="font-body text-editorial-error mt-3 leading-relaxed">{message}</p>
    </section>
  );
}
