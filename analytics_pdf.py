"""Generacion de informes PDF para el dashboard analitico de SportZone.

El modulo no depende de Flask. Recibe el diccionario `analysis` calculado con
pandas y devuelve los bytes de un PDF listo para descargar o guardar.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from textwrap import shorten
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PAGE_SIZE = landscape(A4)
PRIMARY = colors.HexColor("#1A3C5E")
SECONDARY = colors.HexColor("#E8A020")
ACCENT = colors.HexColor("#2ECC71")
DANGER = colors.HexColor("#DB5A42")
PURPLE = colors.HexColor("#7B2D8B")
LIGHT = colors.HexColor("#F4F6F8")
MUTED = colors.HexColor("#65717D")
DARK = colors.HexColor("#17212B")
PALETTE = ["#1A3C5E", "#E8A020", "#2ECC71", "#7B2D8B", "#DB5A42", "#4F7CAC"]


def format_cop(value: Any) -> str:
    """Formatea un valor numerico como pesos colombianos."""
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        number = 0
    return "$" + f"{number:,}".replace(",", ".")


def _chart_image(figure: plt.Figure, width: float, height: float) -> RLImage:
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    buffer.seek(0)
    image = RLImage(buffer, width=width, height=height)
    # Conservar el buffer mientras ReportLab construye el documento.
    image._sportzone_buffer = buffer  # type: ignore[attr-defined]
    return image


def _empty_figure(title: str, message: str = "No hay datos para los filtros seleccionados.") -> plt.Figure:
    figure, axis = plt.subplots(figsize=(9.5, 3.1))
    axis.axis("off")
    axis.set_title(title, loc="left", fontsize=15, fontweight="bold", color="#17212B")
    axis.text(0.5, 0.48, message, ha="center", va="center", fontsize=12, color="#65717D")
    return figure


def _payment_figure(chart: Mapping[str, Any]) -> plt.Figure:
    labels = list(chart.get("labels", []))
    values = [float(value) for value in chart.get("values", [])]
    if not labels or not any(values):
        return _empty_figure("Ventas por metodo de pago")

    figure, axis = plt.subplots(figsize=(9.5, 4.2))
    wedges, _ = axis.pie(
        values,
        startangle=90,
        colors=PALETTE[: len(values)],
        wedgeprops={"width": 0.42, "edgecolor": "white"},
    )
    total = sum(values)
    legend_labels = [
        f"{label}: {format_cop(value)} ({(value / total * 100):.1f}%)"
        for label, value in zip(labels, values)
    ]
    axis.legend(
        wedges,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=False,
        fontsize=9,
    )
    axis.text(0, 0.06, format_cop(total), ha="center", va="center", fontsize=16, fontweight="bold")
    axis.text(0, -0.10, "ventas aprobadas", ha="center", va="center", fontsize=9, color="#65717D")
    axis.set_title("Ventas por metodo de pago", loc="left", fontsize=15, fontweight="bold", color="#17212B")
    figure.tight_layout()
    return figure


def _products_figure(chart: Mapping[str, Any]) -> plt.Figure:
    labels = list(chart.get("labels", []))
    units = [int(value) for value in chart.get("units", [])]
    if not labels or not any(units):
        return _empty_figure("Productos mas vendidos")

    display_labels = [shorten(str(label), width=42, placeholder="...") for label in labels]
    figure, axis = plt.subplots(figsize=(10.4, 4.8))
    axis.barh(display_labels[::-1], units[::-1], color=PALETTE[0])
    axis.set_xlabel("Unidades vendidas")
    axis.set_title("Productos mas vendidos", loc="left", fontsize=15, fontweight="bold", color="#17212B")
    axis.grid(axis="x", alpha=0.18)
    axis.set_axisbelow(True)
    axis.spines[["top", "right", "left"]].set_visible(False)
    for index, value in enumerate(units[::-1]):
        axis.text(value, index, f"  {value}", va="center", fontsize=9)
    figure.tight_layout()
    return figure


def _daily_figure(chart: Mapping[str, Any]) -> plt.Figure:
    labels = list(chart.get("labels", []))
    sales = [float(value) for value in chart.get("sales", [])]
    orders = [int(value) for value in chart.get("orders", [])]
    if not labels or not any(sales):
        return _empty_figure("Evolucion de ventas diarias")

    figure, axis_sales = plt.subplots(figsize=(10.4, 4.2))
    axis_sales.plot(labels, sales, marker="o", linewidth=2.2, color=PALETTE[0], label="Ventas")
    axis_sales.fill_between(labels, sales, alpha=0.10, color=PALETTE[0])
    axis_sales.set_ylabel("Ventas COP")
    axis_sales.tick_params(axis="x", rotation=35)
    axis_sales.grid(axis="y", alpha=0.18)
    axis_sales.spines[["top", "right"]].set_visible(False)

    axis_orders = axis_sales.twinx()
    axis_orders.plot(labels, orders, marker="s", linewidth=1.8, color=PALETTE[1], label="Pedidos")
    axis_orders.set_ylabel("Pedidos")
    axis_orders.spines["top"].set_visible(False)
    axis_sales.set_title("Evolucion de ventas diarias", loc="left", fontsize=15, fontweight="bold", color="#17212B")

    handles_1, labels_1 = axis_sales.get_legend_handles_labels()
    handles_2, labels_2 = axis_orders.get_legend_handles_labels()
    axis_sales.legend(handles_1 + handles_2, labels_1 + labels_2, loc="upper left", frameon=False)
    figure.tight_layout()
    return figure


def _stock_figure(chart: Mapping[str, Any]) -> plt.Figure:
    labels = list(chart.get("labels", []))
    values = [int(value) for value in chart.get("values", [])]
    if not labels:
        return _empty_figure("Productos con menor stock", "No hay productos disponibles.")

    display_labels = [shorten(str(label), width=38, placeholder="...") for label in labels]
    bar_colors = ["#DB5A42" if value <= 5 else "#E8A020" if value <= 10 else "#2ECC71" for value in values]
    figure, axis = plt.subplots(figsize=(10.4, 4.4))
    axis.barh(display_labels[::-1], values[::-1], color=bar_colors[::-1])
    axis.set_xlabel("Unidades disponibles")
    axis.set_title("Productos con menor stock", loc="left", fontsize=15, fontweight="bold", color="#17212B")
    axis.grid(axis="x", alpha=0.18)
    axis.set_axisbelow(True)
    axis.spines[["top", "right", "left"]].set_visible(False)
    figure.tight_layout()
    return figure


def _filter_text(filters: Mapping[str, Any]) -> list[list[str]]:
    start_date = filters.get("start_date") or "Sin limite"
    end_date = filters.get("end_date") or "Sin limite"
    sport = str(filters.get("sport") or "Todos").title()
    payment = str(filters.get("payment_method_name") or "Todos")
    return [
        ["Fecha inicial", str(start_date), "Fecha final", str(end_date)],
        ["Deporte", sport, "Metodo de pago", payment],
    ]


def _header_footer(canvas: Any, doc: SimpleDocTemplate) -> None:
    canvas.saveState()
    width, height = PAGE_SIZE
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, height - 11 * mm, width, 11 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(15 * mm, height - 7 * mm, "SportZone | Informe analitico")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 15 * mm, 8 * mm, f"Pagina {doc.page}")
    canvas.drawString(15 * mm, 8 * mm, "Generado desde MySQL con pandas, matplotlib y ReportLab")
    canvas.restoreState()


def build_analytics_pdf(
    analysis: Mapping[str, Any],
    filters: Mapping[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> bytes:
    """Crea el informe PDF y devuelve su contenido binario."""
    filters = filters or {}
    generated_at = generated_at or datetime.now()
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=17 * mm,
        bottomMargin=15 * mm,
        title="Informe analitico SportZone",
        author="SportZone",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=4 * mm,
    )
    subtitle_style = ParagraphStyle(
        "SportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=MUTED,
        spaceAfter=5 * mm,
    )
    section_style = ParagraphStyle(
        "SportSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=DARK,
        spaceBefore=2 * mm,
        spaceAfter=3 * mm,
    )
    table_text = ParagraphStyle(
        "TableText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=DARK,
        alignment=TA_LEFT,
    )
    table_text_right = ParagraphStyle(
        "TableTextRight",
        parent=table_text,
        alignment=TA_CENTER,
    )

    story: list[Any] = []
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Informe analitico de ventas e inventario", title_style))
    story.append(
        Paragraph(
            "Resumen ejecutivo de ventas aprobadas, productos vendidos, metodos de pago e inventario. "
            f"Fecha de generacion: {generated_at.strftime('%Y-%m-%d %H:%M')}",
            subtitle_style,
        )
    )

    filter_table = Table(_filter_text(filters), colWidths=[31 * mm, 56 * mm, 34 * mm, 90 * mm])
    filter_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DEE5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E1E6EB")),
            ]
        )
    )
    story.append(filter_table)
    story.append(Spacer(1, 5 * mm))

    kpis = analysis.get("kpis", {})
    kpi_cells = [
        ("Ventas de productos", format_cop(kpis.get("sales_total", 0)), "Sin incluir envio"),
        ("Pedidos", str(kpis.get("order_count", 0)), "Pagos aprobados"),
        ("Unidades vendidas", str(kpis.get("units_sold", 0)), "Articulos vendidos"),
        ("Ticket promedio", format_cop(kpis.get("average_ticket", 0)), "Venta por pedido"),
        ("Valor inventario", format_cop(kpis.get("inventory_value", 0)), "Precio por stock"),
        ("Stock critico", str(kpis.get("low_stock_count", 0)), "Productos con 5 o menos"),
    ]
    kpi_data: list[list[Any]] = []
    for row_start in (0, 3):
        row: list[Any] = []
        for label, value, note in kpi_cells[row_start : row_start + 3]:
            row.append(
                Paragraph(
                    f"<font size='8' color='#65717D'>{label}</font><br/>"
                    f"<font size='17' color='#1A3C5E'><b>{value}</b></font><br/>"
                    f"<font size='7.5' color='#65717D'>{note}</font>",
                    styles["Normal"],
                )
            )
        kpi_data.append(row)
    kpi_table = Table(kpi_data, colWidths=[73 * mm, 73 * mm, 73 * mm], rowHeights=[24 * mm, 24 * mm])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8DEE5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8DEE5")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(kpi_table)
    story.append(PageBreak())

    charts = analysis.get("charts", {})
    story.append(Paragraph("Metodos de pago", section_style))
    story.append(
        _chart_image(
            _payment_figure(charts.get("payments", {})),
            width=222 * mm,
            height=88 * mm,
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Productos vendidos", section_style))
    story.append(
        _chart_image(
            _products_figure(charts.get("products", {})),
            width=222 * mm,
            height=94 * mm,
        )
    )
    story.append(Spacer(1, 3 * mm))

    top_products = list(analysis.get("top_products", []))
    product_rows: list[list[Any]] = [
        ["Producto", "Unidades", "Ingreso"]
    ]
    for row in top_products[:10]:
        product_rows.append(
            [
                Paragraph(str(row.get("product_name", "")), table_text),
                Paragraph(str(row.get("units", 0)), table_text_right),
                Paragraph(format_cop(row.get("revenue", 0)), table_text_right),
            ]
        )
    if len(product_rows) == 1:
        product_rows.append(["Sin ventas", "0", "$0"])
    product_table = Table(product_rows, colWidths=[145 * mm, 35 * mm, 43 * mm], repeatRows=1)
    product_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8DEE5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(product_table)
    story.append(PageBreak())

    story.append(Paragraph("Tendencia de ventas", section_style))
    story.append(
        _chart_image(
            _daily_figure(charts.get("daily", {})),
            width=222 * mm,
            height=86 * mm,
        )
    )
    story.append(PageBreak())
    story.append(Paragraph("Control de inventario", section_style))
    story.append(
        _chart_image(
            _stock_figure(charts.get("stock", {})),
            width=222 * mm,
            height=82 * mm,
        )
    )

    document.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()


def _display_value(value: Any, kind: str = "text") -> str:
    """Convierte valores de pandas/SQLite a texto apto para ReportLab."""
    if value is None:
        return ""
    if kind == "money":
        return format_cop(value)
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            pass
    text = str(value)
    if text in {"NaT", "nan", "None"}:
        return ""
    return text


def _dataset_table(
    headers: list[str],
    rows: list[list[Any]],
    widths: list[float],
    styles: Mapping[str, ParagraphStyle],
) -> Table:
    data: list[list[Any]] = [headers]
    for row in rows:
        data.append(
            [
                Paragraph(str(value), styles["table_right"] if index > 0 else styles["table"])
                for index, value in enumerate(row)
            ]
        )
    if len(data) == 1:
        data.append([Paragraph("No hay datos para los filtros seleccionados.", styles["table"])] + [""] * (len(headers) - 1))
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8DEE5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_dataset_pdf(
    dataset: str,
    frames: Mapping[str, Any],
    analysis: Mapping[str, Any],
    filters: Mapping[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> bytes:
    """Genera un PDF individual equivalente a cada exportacion CSV."""
    filters = filters or {}
    generated_at = generated_at or datetime.now()
    if dataset == "completo":
        return build_analytics_pdf(analysis, filters, generated_at)

    titles = {
        "ventas": "Ventas y productos vendidos",
        "pedidos": "Pedidos aprobados",
        "stock": "Estado del inventario",
        "pagos": "Metodos de pago",
        "movimientos": "Kardex de inventario",
    }
    if dataset not in titles:
        raise ValueError("Tipo de informe PDF no valido.")

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=17 * mm,
        bottomMargin=15 * mm,
        title=f"SportZone - {titles[dataset]}",
        author="SportZone",
    )
    sample = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {
        "title": ParagraphStyle(
            "DatasetTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=27,
            textColor=PRIMARY,
            alignment=TA_LEFT,
            spaceAfter=3 * mm,
        ),
        "subtitle": ParagraphStyle(
            "DatasetSubtitle",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=MUTED,
            spaceAfter=4 * mm,
        ),
        "section": ParagraphStyle(
            "DatasetSection",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=DARK,
            spaceBefore=2 * mm,
            spaceAfter=3 * mm,
        ),
        "table": ParagraphStyle(
            "DatasetTable",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10,
            textColor=DARK,
            alignment=TA_LEFT,
        ),
        "table_right": ParagraphStyle(
            "DatasetTableRight",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10,
            textColor=DARK,
            alignment=TA_CENTER,
        ),
    }

    story: list[Any] = [Spacer(1, 4 * mm)]
    story.append(Paragraph(titles[dataset], styles["title"]))
    story.append(
        Paragraph(
            "Descarga generada con los mismos filtros aplicados a la exportacion CSV. "
            f"Fecha de generacion: {generated_at.strftime('%Y-%m-%d %H:%M')}",
            styles["subtitle"],
        )
    )
    filter_table = Table(_filter_text(filters), colWidths=[31 * mm, 56 * mm, 34 * mm, 90 * mm])
    filter_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DEE5")),
            ]
        )
    )
    story.extend([filter_table, Spacer(1, 5 * mm)])

    charts = analysis.get("charts", {})

    if dataset == "ventas":
        story.append(Paragraph("Productos mas vendidos", styles["section"]))
        story.append(_chart_image(_products_figure(charts.get("products", {})), 222 * mm, 89 * mm))
        story.append(PageBreak())
        story.append(Paragraph("Detalle de ventas", styles["section"]))
        frame = frames["items"].sort_values("created_at", ascending=False).head(100)
        rows = [
            [
                _display_value(row.product_name),
                _display_value(row.sport).title(),
                _display_value(row.quantity),
                _display_value(row.unit_price, "money"),
                _display_value(row.line_total, "money"),
                _display_value(row.created_at),
            ]
            for row in frame.itertuples(index=False)
        ]
        story.append(_dataset_table(
            ["Producto", "Deporte", "Cantidad", "Precio", "Total", "Fecha"],
            rows,
            [91 * mm, 23 * mm, 21 * mm, 28 * mm, 31 * mm, 34 * mm],
            styles,
        ))

    elif dataset == "pedidos":
        story.append(Paragraph("Resumen de pedidos", styles["section"]))
        story.append(_chart_image(_daily_figure(charts.get("daily", {})), 222 * mm, 86 * mm))
        story.append(PageBreak())
        frame = frames["orders"].sort_values("created_at", ascending=False).head(100)
        rows = [
            [
                f"#{_display_value(row.order_id)}",
                _display_value(row.customer_name),
                _display_value(row.payment_method),
                _display_value(row.total, "money"),
                _display_value(row.order_status).title(),
                _display_value(row.created_at),
            ]
            for row in frame.itertuples(index=False)
        ]
        story.append(_dataset_table(
            ["Pedido", "Cliente", "Metodo", "Total", "Estado", "Fecha"],
            rows,
            [23 * mm, 59 * mm, 43 * mm, 31 * mm, 28 * mm, 42 * mm],
            styles,
        ))

    elif dataset == "stock":
        story.append(Paragraph("Productos con menor stock", styles["section"]))
        story.append(_chart_image(_stock_figure(charts.get("stock", {})), 222 * mm, 83 * mm))
        story.append(PageBreak())
        frame = frames["stock"].sort_values(["stock", "name"]).head(120)
        rows = [
            [
                _display_value(row.name),
                _display_value(row.brand),
                _display_value(row.sport).title(),
                _display_value(row.product_type),
                _display_value(row.stock),
                _display_value(row.inventory_value, "money"),
            ]
            for row in frame.itertuples(index=False)
        ]
        story.append(_dataset_table(
            ["Producto", "Marca", "Deporte", "Tipo", "Stock", "Valor inventario"],
            rows,
            [77 * mm, 34 * mm, 25 * mm, 42 * mm, 20 * mm, 31 * mm],
            styles,
        ))

    elif dataset == "pagos":
        story.append(Paragraph("Ventas por metodo de pago", styles["section"]))
        story.append(_chart_image(_payment_figure(charts.get("payments", {})), 222 * mm, 88 * mm))
        story.append(PageBreak())
        frame = frames["payments"].sort_values("paid_at", ascending=False).head(100)
        rows = [
            [
                f"#{_display_value(row.order_id)}",
                _display_value(row.payment_method),
                _display_value(row.transaction_reference),
                _display_value(row.amount, "money"),
                _display_value(row.status).title(),
                _display_value(row.paid_at),
            ]
            for row in frame.itertuples(index=False)
        ]
        story.append(_dataset_table(
            ["Pedido", "Metodo", "Referencia", "Valor", "Estado", "Fecha"],
            rows,
            [23 * mm, 44 * mm, 64 * mm, 31 * mm, 25 * mm, 42 * mm],
            styles,
        ))

    elif dataset == "movimientos":
        story.append(Paragraph("Movimientos de inventario", styles["section"]))
        frame = frames["movements"].sort_values(["created_at", "id"], ascending=False).head(150)
        rows = [
            [
                _display_value(row.product_name),
                _display_value(row.movement_type).replace("_", " ").title(),
                _display_value(row.quantity_change),
                _display_value(row.stock_before),
                _display_value(row.stock_after),
                _display_value(row.responsible),
                _display_value(row.created_at),
            ]
            for row in frame.itertuples(index=False)
        ]
        story.append(_dataset_table(
            ["Producto", "Movimiento", "Cambio", "Antes", "Despues", "Responsable", "Fecha"],
            rows,
            [70 * mm, 35 * mm, 19 * mm, 19 * mm, 20 * mm, 35 * mm, 33 * mm],
            styles,
        ))

    document.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
