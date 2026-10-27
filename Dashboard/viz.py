import math
from collections.abc import Callable

import altair as alt
import pandas as pd
import streamlit as st

from Dashboard import charts

alt.data_transformers.disable_max_rows()

ROW_STEP = 26


def limit_categories(
    df: pd.DataFrame, column: str, keep: int = 7, other: str = "Other"
) -> pd.DataFrame:
    out = df.copy()
    top = out[column].value_counts().nlargest(keep).index
    out[column] = out[column].where(out[column].isin(top), other)
    return out


def categorical_scale(domain: list[str]) -> alt.Scale:
    return alt.Scale(domain=domain, range=charts.SERIES[: max(len(domain), 1)])


def verdict_scale() -> alt.Scale:
    colors = charts.VERDICT_COLORS
    return alt.Scale(domain=list(colors), range=list(colors.values()))


def themed(chart):
    pal = charts.palette()
    return (
        chart.configure(background="transparent")
        .configure_axis(
            labelColor=pal["text"],
            titleColor=pal["text"],
            gridColor=pal["grid"],
            domainColor=pal["grid"],
            tickColor=pal["grid"],
            labelFontSize=12,
            titleFontSize=12,
            titleFontWeight="normal",
            titlePadding=10,
            tickCount=6,
        )
        .configure_view(stroke=None)
        .configure_legend(
            labelColor=pal["text"],
            titleColor=pal["text"],
            labelFontSize=12,
            orient="top",
            direction="horizontal",
            symbolType="square",
            padding=4,
        )
        .configure_title(color=pal["text"], anchor="start", fontSize=16, fontWeight=600)
    )


def show(chart, height: int | None = None) -> None:
    if height is not None:
        chart = chart.properties(height=height)
    st.altair_chart(themed(chart), theme=None, width="stretch")


def axis_format(fmt: str | None) -> alt.Axis:
    return alt.Axis(format=fmt) if fmt else alt.Axis()


def decade_ticks(values: pd.Series) -> list[float]:
    positive = values[values > 0]
    if positive.empty:
        return [1, 10]
    low = int(math.floor(math.log10(positive.min())))
    high = int(math.ceil(math.log10(positive.max())))
    return [10.0**power for power in range(low, high + 1)]


def log_scale_and_axis(values: pd.Series, fmt: str | None) -> tuple[alt.Scale, alt.Axis]:
    ticks = decade_ticks(values)
    scale = alt.Scale(type="log", domain=[ticks[0], ticks[-1]])
    return scale, alt.Axis(values=ticks, format=fmt or "~s")


def color_encoding(
    df: pd.DataFrame,
    color: str | None,
    scale: alt.Scale | None = None,
    title: str | None = None,
    show_legend: bool = True,
):
    if color is None:
        return alt.value(charts.SERIES[0])
    domain = sorted(df[color].dropna().astype(str).unique().tolist())
    legend = alt.Legend(title=title) if show_legend else None
    return alt.Color(f"{color}:N", scale=scale or categorical_scale(domain), legend=legend)


def legend_highlight(color: str | None):
    if color is None:
        return None
    return alt.selection_point(fields=[color], bind="legend")


def with_highlight(chart, selection, color: str | None):
    if selection is None:
        return chart
    return chart.add_params(selection).encode(
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.25))
    )


def reference_rule(value: float, orient: str = "x") -> alt.Chart:
    frame = pd.DataFrame({"value": [value]})
    return (
        alt.Chart(frame)
        .mark_rule(strokeDash=[4, 4], color=charts.MUTED, strokeWidth=1.5)
        .encode(**{orient: alt.X("value:Q") if orient == "x" else alt.Y("value:Q")})
    )


def hbar(
    df: pd.DataFrame,
    y: str,
    x: str,
    *,
    color: str | None = None,
    scale: alt.Scale | None = None,
    label: Callable[[float], str] | None = None,
    tooltip: list | None = None,
    x_title: str | None = None,
    x_format: str | None = None,
    ascending: bool = False,
    rule: float | None = None,
    legend_title: str | None = None,
    x_domain: tuple[float, float] | None = None,
    show_legend: bool = True,
) -> alt.LayerChart:
    data = df.copy()
    order = data.sort_values(x, ascending=ascending)[y].tolist()
    data["_label"] = data[x].map(label) if label else data[x].map(lambda v: f"{v:,.0f}")
    selection = legend_highlight(color)

    base = alt.Chart(data).encode(
        y=alt.Y(f"{y}:N", sort=order, title=None, axis=alt.Axis(labelLimit=280, ticks=False)),
        x=alt.X(
            f"{x}:Q",
            title=x_title,
            axis=axis_format(x_format),
            scale=alt.Scale(domain=list(x_domain)) if x_domain else alt.Scale(),
        ),
    )
    bars = base.mark_bar(cornerRadiusEnd=3).encode(
        color=color_encoding(data, color, scale, legend_title, show_legend),
        tooltip=tooltip or [alt.Tooltip(f"{y}:N"), alt.Tooltip(f"{x}:Q", format=",.2f")],
    )
    bars = with_highlight(bars, selection, color)

    negative = data[data[x] < 0]
    positive = data[data[x] >= 0]
    text_args = dict(fontSize=12, color=charts.palette()["text"])
    layers = [bars]
    for frame, align, dx in ((positive, "left", 5), (negative, "right", -5)):
        if frame.empty:
            continue
        layers.append(
            alt.Chart(frame)
            .mark_text(align=align, dx=dx, **text_args)
            .encode(y=alt.Y(f"{y}:N", sort=order), x=alt.X(f"{x}:Q"), text="_label:N")
        )
    if rule is not None:
        layers.append(reference_rule(rule))
    return alt.layer(*layers).properties(height=alt.Step(ROW_STEP))


def vbar_grouped(
    df: pd.DataFrame,
    x: str,
    y: str,
    group: str,
    *,
    order: list[str] | None = None,
    scale: alt.Scale | None = None,
    label: Callable[[float], str] | None = None,
    y_title: str | None = None,
    y_format: str | None = None,
    tooltip: list | None = None,
) -> alt.LayerChart:
    data = df.copy()
    data[x] = data[x].astype(str)
    data["_label"] = data[y].map(label) if label else data[y].map(lambda v: f"{v:,.0f}")
    groups = sorted(data[group].unique().tolist())
    selection = legend_highlight(group)

    base = alt.Chart(data).encode(
        x=alt.X(f"{x}:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, ticks=False)),
        xOffset=alt.XOffset(f"{group}:N"),
        y=alt.Y(f"{y}:Q", title=y_title, axis=axis_format(y_format)),
    )
    bars = base.mark_bar(cornerRadiusEnd=3).encode(
        color=color_encoding(data, group, scale or categorical_scale(groups)),
        tooltip=tooltip or [alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{group}:N"),
                            alt.Tooltip(f"{y}:Q", format=",.2f")],
    )
    bars = with_highlight(bars, selection, group)
    text = base.mark_text(dy=-8, fontSize=11, color=charts.palette()["text"]).encode(
        text="_label:N"
    )
    return alt.layer(bars, text)


def stacked_hbar(
    df: pd.DataFrame,
    y: str,
    x: str,
    color: str,
    *,
    scale: alt.Scale | None = None,
    x_format: str = "%",
    tooltip: list | None = None,
) -> alt.Chart:
    groups = sorted(df[color].unique().tolist())
    selection = legend_highlight(color)
    chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y(f"{y}:N", title=None, axis=alt.Axis(ticks=False, labelLimit=280)),
        x=alt.X(f"{x}:Q", title=None, stack="normalize", axis=alt.Axis(format=x_format)),
        color=color_encoding(df, color, scale or categorical_scale(groups)),
        tooltip=tooltip or [alt.Tooltip(f"{y}:N"), alt.Tooltip(f"{color}:N"),
                            alt.Tooltip(f"{x}:Q", format=".0%")],
    )
    return with_highlight(chart, selection, color).properties(height=alt.Step(ROW_STEP))


def scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    *,
    color: str | None = None,
    scale: alt.Scale | None = None,
    size: str | None = None,
    tooltip: list | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    log_x: bool = False,
    log_y: bool = False,
    x_format: str | None = None,
    y_format: str | None = None,
    label: str | None = None,
    label_top: int = 0,
    label_by: str | None = None,
    legend_title: str | None = None,
    shared_log_range: pd.Series | None = None,
) -> alt.LayerChart:
    selection = legend_highlight(color)
    if log_x:
        x_scale, x_axis = log_scale_and_axis(
            df[x] if shared_log_range is None else shared_log_range, x_format
        )
    else:
        x_scale, x_axis = alt.Scale(zero=False), axis_format(x_format)
    if log_y:
        y_scale, y_axis = log_scale_and_axis(
            df[y] if shared_log_range is None else shared_log_range, y_format
        )
    else:
        y_scale, y_axis = alt.Scale(zero=False), axis_format(y_format)
    x_enc = alt.X(f"{x}:Q", title=x_title, scale=x_scale, axis=x_axis)
    y_enc = alt.Y(f"{y}:Q", title=y_title, scale=y_scale, axis=y_axis)

    points = (
        alt.Chart(df)
        .mark_circle(opacity=0.8, stroke=charts.palette()["grid"], strokeWidth=1)
        .encode(x=x_enc, y=y_enc, color=color_encoding(df, color, scale, legend_title))
    )
    if tooltip:
        points = points.encode(tooltip=tooltip)
    if size:
        points = points.encode(
            size=alt.Size(f"{size}:Q", scale=alt.Scale(range=[60, 1100]), legend=None)
        )
    else:
        points = points.encode(size=alt.value(90))
    layers = [with_highlight(points, selection, color)]

    if label and label_top:
        ranked = df.nlargest(label_top, label_by or size or y)
        layers.append(
            alt.Chart(ranked)
            .mark_text(dy=-14, fontSize=11, color=charts.palette()["text"])
            .encode(x=x_enc, y=y_enc, text=f"{label}:N")
        )
    return alt.layer(*layers)


def default_line_tooltip(x: str, y: str, color: str | None) -> list:
    tips = [alt.Tooltip(f"{x}:T", format="%d %b %Y"), alt.Tooltip(f"{y}:Q", format=",.0f")]
    if color:
        tips.insert(0, alt.Tooltip(f"{color}:N"))
    return tips


def line(
    df: pd.DataFrame,
    x: str,
    y: str,
    *,
    color: str | None = None,
    scale: alt.Scale | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    y_format: str | None = "~s",
    tooltip: list | None = None,
    legend_title: str | None = None,
) -> alt.LayerChart:
    nearest = alt.selection_point(nearest=True, on="pointerover", fields=[x], empty=False)
    dates = [
        alt.DateTime(year=d.year, month=d.month, date=d.day)
        for d in sorted(pd.to_datetime(df[x]).dt.normalize().unique())
    ]
    base = alt.Chart(df).encode(
        x=alt.X(
            f"{x}:T",
            title=x_title,
            scale=alt.Scale(padding=24),
            axis=alt.Axis(format="%d %b", grid=False, values=dates),
        ),
        y=alt.Y(f"{y}:Q", title=y_title, axis=alt.Axis(format=y_format)),
        color=color_encoding(df, color, scale, legend_title),
    )
    lines = base.mark_line(strokeWidth=2.5)
    selectors = base.mark_point(size=250).encode(opacity=alt.value(0)).add_params(nearest)
    selectors = selectors.encode(tooltip=tooltip or default_line_tooltip(x, y, color))
    points = base.mark_point(filled=True, size=80).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0.0001))
    )
    rules = (
        alt.Chart(df)
        .mark_rule(color=charts.palette()["grid"])
        .encode(x=alt.X(f"{x}:T"))
        .transform_filter(nearest)
    )
    return alt.layer(lines, selectors, points, rules)


def heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    value: str,
    *,
    value_title: str | None = None,
    x_order: list[str] | None = None,
    y_order: list[str] | None = None,
) -> alt.Chart:
    return alt.Chart(df).mark_rect(cornerRadius=2).encode(
        x=alt.X(f"{x}:N", sort=x_order, title=None, axis=alt.Axis(labelAngle=-40, ticks=False)),
        y=alt.Y(f"{y}:N", sort=y_order, title=None, axis=alt.Axis(ticks=False)),
        color=alt.Color(
            f"{value}:Q",
            scale=alt.Scale(range=charts.palette()["blue"]),
            legend=alt.Legend(title=value_title, orient="right", direction="vertical"),
        ),
        tooltip=[alt.Tooltip(f"{y}:N"), alt.Tooltip(f"{x}:N"),
                 alt.Tooltip(f"{value}:Q", format=",.0f", title=value_title)],
    )


def boxplot(
    df: pd.DataFrame, group: str, value: str, *, order: list[str], x_title: str | None = None
) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_boxplot(
            extent=1.5,
            outliers=False,
            size=16,
            color=charts.SERIES[0],
            median=dict(color=charts.palette()["text"]),
            rule=dict(color=charts.MUTED),
            ticks=dict(color=charts.MUTED),
        )
        .encode(
            y=alt.Y(f"{group}:N", sort=order, title=None, axis=alt.Axis(ticks=False)),
            x=alt.X(f"{value}:Q", title=x_title),
        )
        .properties(height=alt.Step(ROW_STEP + 6))
    )
