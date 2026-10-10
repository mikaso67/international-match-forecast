from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
FORECAST_DIR = ROOT / "reports" / "forecasts"
FORECAST_DATE = "2026-10-07"
REPO_URL = "https://github.com/mikaso67/international-match-forecast"
PUBLISHED_FILE_URL = f"{REPO_URL}/blob/5daf904/reports/forecasts/nations_league_2026_standings_{FORECAST_DATE}.csv"

ACCENT = "#1D5BD6"
INK = "#1B1F27"
MUTED = "#5E6573"
DRAW = "#CBD1DA"

LEAGUE_NOTES = {
    "A": "The top two of each group reach the quarter-finals. The last team goes down to League B.",
    "B": "Group winners go up to League A. The last team goes down to League C.",
    "C": "Group winners go up to League B. The two weakest last-placed teams go down to League D.",
    "D": "Group winners go up to League C.",
}
ROUNDS = {
    "round_of_32": "Last 32",
    "round_of_16": "Last 16",
    "quarter_final": "Quarter-final",
    "semi_final": "Semi-final",
    "final": "Final",
    "champion": "Winner",
}
MODEL_LABELS = {
    "uniform": "One third each",
    "frequency_by_venue": "Past frequencies",
    "elo_logistic": "Elo rating",
    "poisson": "Goal model",
}


@st.cache_data
def load_data():
    return {
        "standings": pd.read_csv(FORECAST_DIR / f"nations_league_2026_standings_{FORECAST_DATE}.csv"),
        "fixtures": pd.read_csv(FORECAST_DIR / f"nations_league_2026_matches_{FORECAST_DATE}.csv", parse_dates=["date"]),
        "world_cup": pd.read_csv(APP_DIR / "data" / "world_cup_2026_backtest.csv"),
        "scores": pd.read_csv(APP_DIR / "data" / "test_scores.csv"),
        "calibration": pd.read_csv(APP_DIR / "data" / "test_calibration.csv"),
    }


def percent(p):
    if p < 0.005:
        return "0%" if p == 0 else "<1%"
    return f"{p:.0%}"


def shaded_cell(p, extra_class=""):
    alpha = min(1.0, p ** 0.75)
    color = "#FFFFFF" if alpha > 0.55 else INK
    style = f"background: rgba(29, 91, 214, {alpha:.3f}); color: {color};"
    return f'<td class="{extra_class}" style="{style}">{percent(p)}</td>'


def group_table(group):
    places = [c for c in group.columns if c.startswith("p") and group[c].notna().any()]
    expected_place = sum(group[c].fillna(0) * (i + 1) for i, c in enumerate(places))
    group = group.assign(expected=expected_place).sort_values("expected")
    header = "".join(f"<th>{i + 1}{['st', 'nd', 'rd', 'th'][i]}</th>" for i in range(len(places)))
    rows = "".join(
        f'<tr><td class="team">{row.team}</td>' + "".join(shaded_cell(getattr(row, c)) for c in places) + "</tr>"
        for row in group.itertuples()
    )
    return f'<table class="places"><tr><th></th>{header}</tr>{rows}</table>'


def fixture_row(match):
    segments = [("h", match.p_H), ("d", match.p_D), ("a", match.p_A)]
    strip = "".join(
        f'<div class="{name}" style="flex: {p:.4f};">{percent(p) if p >= 0.12 else ""}</div>' for name, p in segments
    )
    return (
        f'<div class="fixture"><div class="home">{match.home_team}</div>'
        f'<div class="strip">{strip}</div><div class="away">{match.away_team}</div></div>'
    )


def masthead():
    st.markdown(
        """
        <div class="masthead">
            <h1>International Match Forecast</h1>
            <p>Probabilities for international football matches and tournaments, from a statistical model of goals.
            Forecasts are published before the games and checked against what happens.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nations_league_tab(data):
    st.markdown(
        f'<div class="stamp">Forecast published on 8 October 2026 with every result up to 6 October. '
        f'Matchdays 5 and 6 are played from 12 to 17 November. '
        f'<a href="{PUBLISHED_FILE_URL}">See the published file</a>.</div>',
        unsafe_allow_html=True,
    )
    league = st.segmented_control("League", ["A", "B", "C", "D"], default="A", format_func=lambda x: f"League {x}")
    league = league or "A"
    st.markdown(f'<p class="lede">{LEAGUE_NOTES[league]} Each cell is the chance of finishing in that place, '
                f'from 10,000 simulations of the remaining games.</p>', unsafe_allow_html=True)

    standings = data["standings"]
    in_league = standings[standings["group"].str.startswith(league)]
    columns = st.columns(2)
    for i, (group, teams) in enumerate(in_league.groupby("group")):
        with columns[i % 2]:
            st.markdown(f'<div class="group-title">Group {group}</div>{group_table(teams)}', unsafe_allow_html=True)

    st.markdown('<div class="group-title">Games to come</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="legend"><span style="--swatch: {ACCENT}">Home win</span>'
        f'<span style="--swatch: {DRAW}">Draw</span><span style="--swatch: #2D3442">Away win</span></div>',
        unsafe_allow_html=True,
    )
    fixtures = data["fixtures"]
    fixtures = fixtures[fixtures["group"].str.startswith(league)].sort_values(["date", "group"])
    html = ""
    for day, games in fixtures.groupby("date"):
        html += f'<div class="day">{day:%A %d November}</div>' + "".join(fixture_row(g) for g in games.itertuples())
    st.markdown(html, unsafe_allow_html=True)


def path_table(world_cup):
    header = "".join(f"<th>{label}</th>" for label in ROUNDS.values())
    rows = ""
    for row in world_cup.itertuples():
        reached = [r for r in ROUNDS if getattr(row, f"reached_{r}") == 1]
        last = reached[-1] if reached else None
        cells = ""
        for r in ROUNDS:
            marker = "won" if r == "champion" and r == last else ("out" if r == last else "")
            cells += shaded_cell(getattr(row, r), marker)
        note = "" if reached else ' <span style="color: #5E6573; font-weight: 500;">out in the groups</span>'
        rows += f'<tr><td class="team">{row.team}{note}</td>{cells}</tr>'
    return f'<table class="path"><tr><th></th>{header}</tr>{rows}</table>'


def world_cup_tab(data):
    st.markdown(
        '<p class="lede">On 10 June 2026, the day before kick-off, the model played the whole World Cup '
        '10,000 times. Each cell is how often a team reached that round. '
        'The outline shows how far it really went.</p>',
        unsafe_allow_html=True,
    )
    world_cup = data["world_cup"].sort_values("champion", ascending=False)
    show_all = st.toggle("Show all 48 teams")
    st.markdown(path_table(world_cup if show_all else world_cup.head(16)), unsafe_allow_html=True)
    st.markdown(
        """
        <p class="verdict">The final was played by the two teams the model rated most likely to reach it,
        Argentina (26%) and Spain (21%). Spain won the title as the second favourite.</p>
        <p class="verdict">The four semi-finalists all had a higher chance of getting there than the four other
        quarter-finalists. The biggest misses were Uruguay, out in the groups with a 89% chance of going through,
        and Brazil, beaten by Norway in the last 16.</p>
        """,
        unsafe_allow_html=True,
    )


def calibration_chart(calibration):
    names = {"H": "Home win", "D": "Draw", "A": "Away win"}
    data = calibration[calibration["n_matches"] >= 20].assign(outcome=lambda d: d["outcome"].map(names))
    diagonal = pd.DataFrame({"predicted": [0, 1], "observed": [0, 1]})
    charts = []
    for name in names.values():
        base = alt.Chart(data[data["outcome"] == name])
        line = base.mark_line(color=ACCENT, strokeWidth=2, point=alt.OverlayMarkDef(size=60, color=ACCENT)).encode(
            x=alt.X("predicted:Q", title="Announced", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%")),
            y=alt.Y("observed:Q", title="Happened", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%")),
            tooltip=[alt.Tooltip("predicted:Q", format=".0%", title="Announced"),
                     alt.Tooltip("observed:Q", format=".0%", title="Happened"),
                     alt.Tooltip("n_matches:Q", title="Games")],
        )
        reference = alt.Chart(diagonal).mark_line(color="#9AA1AD", strokeDash=[4, 4]).encode(x="predicted", y="observed")
        charts.append((reference + line).properties(width=230, height=230, title=name))
    return (
        alt.hconcat(*charts)
        .configure(font="Barlow, Helvetica, Arial, sans-serif")
        .configure_title(font="Barlow Condensed, Arial Narrow, sans-serif", fontSize=17, fontWeight=600, color=INK, anchor="start")
        .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#E4E7EC", domainColor="#C3C8D0", labelFontSize=12)
        .configure_view(stroke=None)
    )


def reliability_tab(data):
    scores = data["scores"].set_index("model")
    share = np.exp(-scores["log_loss"])
    n_matches = int(scores["n_matches"].iloc[0])
    st.markdown(
        f'<p class="lede">I tested the model on {n_matches:,} matches played from January 2024 to August 2026, '
        f'none of which was used to build it. A useful way to read the result: on average, how much probability '
        f'did each approach give to the result that actually happened?</p>',
        unsafe_allow_html=True,
    )
    rows = ""
    for model, label in MODEL_LABELS.items():
        final = " final" if model == "poisson" else ""
        rows += (
            f'<div class="share-row{final}"><div class="label">{label}</div>'
            f'<div class="bar"><div style="width: {share[model] / 0.5:.1%};"></div></div>'
            f'<div class="value">{share[model]:.1%}</div></div>'
        )
    st.markdown(rows, unsafe_allow_html=True)
    st.markdown(
        '<p class="lede" style="margin-top: 1rem;">The gap between the Elo rating and the goal model looks small, '
        'but over 2,583 games it is more than four times its standard error. Football is noisy: '
        'no model gets close to 100%.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="group-title">Do the probabilities mean what they say?</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="lede">I group the games by the probability the model announced, then check how often the result '
        'really happened. On the dashed line, an announced 60% happens 60% of the time.</p>',
        unsafe_allow_html=True,
    )
    st.altair_chart(calibration_chart(data["calibration"]), theme=None)


def method_tab():
    st.markdown(
        f"""
        <div class="lede">
        <p><b>Data.</b> About 47,000 men's international matches since 1872, cleaned in SQL. Regional and non-FIFA
        sides are removed, and extra-time goals are taken out so every game is scored over 90 minutes.</p>
        <p><b>Model.</b> Each team gets an attack and a defence strength, estimated from its last eight years of
        games, with recent games counting more. Expected goals for a match come from both teams' strengths and home
        advantage. I compared it with an Elo rating, a Dixon-Coles correction and gradient boosting: none did
        clearly better, so I kept the simplest.</p>
        <p><b>Simulation.</b> A tournament is played 10,000 times. Group games follow the real format and
        tie-breakers. Knockout games go to extra time, then to penalties, which are close to a coin flip in the data.</p>
        <p><b>Limits.</b> The model only sees results: no line-ups, injuries or player ratings. It slightly
        underestimates draws between evenly matched teams.</p>
        <p>This is a sports analytics and statistics project. It uses no betting odds and is not meant for
        gambling. Code and data pipeline: <a href="{REPO_URL}">{REPO_URL.removeprefix("https://")}</a>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="International Match Forecast", page_icon=":material/sports_soccer:", layout="centered")
    st.markdown(f"<style>{(APP_DIR / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    data = load_data()
    masthead()
    nations, world_cup, reliability, method = st.tabs(["Nations League", "World Cup 2026", "Reliability", "Method"])
    with nations:
        nations_league_tab(data)
    with world_cup:
        world_cup_tab(data)
    with reliability:
        reliability_tab(data)
    with method:
        method_tab()


main()
