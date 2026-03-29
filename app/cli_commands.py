"""
CLI de SocioAI - comandos de linea de comandos.
Uso: python -m app.cli_commands [COMANDO] [OPCIONES]
"""

from __future__ import annotations


import click

from analysis.benchmark import resumen_benchmark
from analysis.lector_tb import obtener_resumen_tb
from analysis.ranking_areas import calcular_ranking_areas
from analysis.ratios import resumen_ratios
from analysis.tendencias import resumen_tendencias
from core.paths import cliente_existe, listar_clientes
from domain.services.leer_perfil import leer_perfil


@click.group()
def main() -> None:
    """SocioAI - Plataforma inteligente de auditoria financiera."""


@main.command("clientes")
def cmd_clientes() -> None:
    """Lista todos los clientes disponibles."""
    clientes = listar_clientes()
    if not clientes:
        click.echo("No hay clientes disponibles.")
        return
    click.echo(f"\nClientes disponibles ({len(clientes)}):\n")
    for cliente in clientes:
        click.echo(f"  - {cliente}")
    click.echo()


@main.command("perfil")
@click.argument("cliente")
def cmd_perfil(cliente: str) -> None:
    """Muestra el perfil de un cliente."""
    if not cliente_existe(cliente):
        click.echo(f"Error: cliente '{cliente}' no encontrado.", err=True)
        raise SystemExit(1)

    perfil = leer_perfil(cliente)
    if not perfil:
        click.echo("No se pudo cargar el perfil.", err=True)
        raise SystemExit(1)

    info = perfil.get("cliente", {})
    encargo = perfil.get("encargo", {})
    click.echo(f"\nCliente:  {info.get('nombre_legal', 'N/A')}")
    click.echo(f"RUC:      {info.get('ruc', 'N/A')}")
    click.echo(f"Sector:   {info.get('sector', 'N/A')}")
    click.echo(f"Periodo:  {encargo.get('anio_activo', 'N/A')}")
    click.echo(f"Marco:    {encargo.get('marco_referencial', 'N/A')}")
    click.echo(f"Fase:     {encargo.get('fase_actual', 'N/A')}\n")


@main.command("balance")
@click.argument("cliente")
def cmd_balance(cliente: str) -> None:
    """Muestra el resumen del balance del cliente."""
    if not cliente_existe(cliente):
        click.echo(f"Error: cliente '{cliente}' no encontrado.", err=True)
        raise SystemExit(1)

    resumen = obtener_resumen_tb(cliente)
    if not resumen:
        click.echo("No se pudo cargar el TB.", err=True)
        raise SystemExit(1)

    click.echo(f"\nBalance - {cliente}\n")
    for tipo, total in resumen.items():
        click.echo(f"  {tipo:<15} ${float(total):>15,.2f}")
    click.echo()


@main.command("ranking")
@click.argument("cliente")
@click.option("--top", default=5, help="Numero de areas a mostrar (default: 5)")
def cmd_ranking(cliente: str, top: int) -> None:
    """Muestra el ranking de areas por riesgo."""
    if not cliente_existe(cliente):
        click.echo(f"Error: cliente '{cliente}' no encontrado.", err=True)
        raise SystemExit(1)

    ranking = calcular_ranking_areas(cliente)
    if ranking is None or ranking.empty:
        click.echo("No se pudo calcular el ranking.", err=True)
        raise SystemExit(1)

    click.echo(f"\nRanking de areas - {cliente}\n")
    for _, row in ranking.head(top).iterrows():
        click.echo(
            f"  {int(row.get('ranking', 0)):>2}. "
            f"{str(row.get('area', '')):>8} "
            f"{str(row.get('nombre', '')):<35} "
            f"Score: {float(row.get('score_riesgo', 0)):>6.2f}"
        )
    click.echo()


@main.command("ratios")
@click.argument("cliente")
def cmd_ratios(cliente: str) -> None:
    """Muestra ratios financieros y benchmark del cliente."""
    if not cliente_existe(cliente):
        click.echo(f"Error: cliente '{cliente}' no encontrado.", err=True)
        raise SystemExit(1)

    ratios = resumen_ratios(cliente)
    benchmark = resumen_benchmark(cliente)
    if not ratios:
        click.echo("Sin datos suficientes para ratios.", err=True)
        raise SystemExit(1)

    click.echo(f"\nRatios financieros - {cliente}\n")
    for ratio in ratios:
        valor = ratio.get("valor")
        valor_str = f"{float(valor):.4f}" if valor is not None else "N/A"
        click.echo(f"  {ratio['ratio']:<22} {valor_str:>10}  " f"{ratio.get('interpretacion', '')}")

    if benchmark.get("total", 0) > 0:
        click.echo(
            f"\nBenchmark: {benchmark['ok']} OK | "
            f"{benchmark['alerta']} Alerta | "
            f"{benchmark['critico']} Critico\n"
        )


@main.command("tendencias")
@click.argument("cliente")
def cmd_tendencias(cliente: str) -> None:
    """Muestra cuentas con tendencias que requieren atencion."""
    if not cliente_existe(cliente):
        click.echo(f"Error: cliente '{cliente}' no encontrado.", err=True)
        raise SystemExit(1)

    resumen = resumen_tendencias(cliente)
    if not resumen:
        click.echo("Sin datos de tendencias.", err=True)
        raise SystemExit(1)

    click.echo(f"\nTendencias - {cliente}\n")
    click.echo(f"  Total cuentas:     {resumen['total_cuentas']}")
    click.echo(f"  Cuentas en alerta: {resumen['cuentas_alerta']}")
    conteo = resumen.get("conteo_por_tendencia", {})
    for tendencia, count in sorted(conteo.items(), key=lambda item: item[1], reverse=True):
        click.echo(f"  {tendencia:<28} {count:>4}")
    click.echo()


@main.command("briefing")
@click.argument("cliente")
@click.argument("codigo_ls")
@click.option(
    "--etapa",
    default="planificacion",
    type=click.Choice(["planificacion", "ejecucion", "cierre"]),
    help="Etapa de auditoria",
)
def cmd_briefing(cliente: str, codigo_ls: str, etapa: str) -> None:
    """Genera briefing de auditoria para un area (sin IA)."""
    if not cliente_existe(cliente):
        click.echo(f"Error: cliente '{cliente}' no encontrado.", err=True)
        raise SystemExit(1)

    try:
        from llm.briefing_llm import generar_briefing_area_llm

        resultado = generar_briefing_area_llm(cliente, codigo_ls, etapa)
        click.echo(resultado)
    except Exception as exc:
        click.echo(f"Error generando briefing: {exc}", err=True)
        raise SystemExit(1)


@main.command("indexar")
@click.option("--forzar", is_flag=True, default=False, help="Reindexar aunque ya exista contenido.")
def cmd_indexar(forzar: bool) -> None:
    """Indexa la base de conocimiento normativo en ChromaDB."""
    click.echo("\nIniciando indexacion de base normativa...")
    try:
        from infra.rag.retriever import inicializar_rag

        resultado = inicializar_rag(forzar=forzar)
        estado = resultado.get("estado", "desconocido")
        total = resultado.get("total_chunks", 0)
        if estado == "ya_indexado":
            click.echo(f"Ya indexado: {total} chunks. Usa --forzar para reindexar.")
        elif estado == "indexado":
            click.echo(f"Indexacion completa: {total} chunks indexados.")
        else:
            click.echo(f"Estado: {estado}")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@main.command("buscar")
@click.argument("consulta")
@click.option("--n", default=3, help="Numero de resultados (default: 3)")
def cmd_buscar(consulta: str, n: int) -> None:
    """Busca en la base normativa indexada."""
    try:
        from infra.rag.retriever import recuperar_contexto_normativo

        contexto = recuperar_contexto_normativo(consulta, n_resultados=n)
        if contexto:
            click.echo(contexto)
        else:
            click.echo("Sin resultados. Ejecuta primero: python -m app.cli_commands indexar")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)


if __name__ == "__main__":
    main()
