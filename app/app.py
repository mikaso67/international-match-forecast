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
OUTCOMES = ["H", "D", "A"]
OUTCOME_LABELS = {"H": "Home win", "D": "Draw", "A": "Away win"}
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
        "predictions": pd.read_csv(APP_DIR / "data" / "test_predictions.csv", parse_dates=["date"]),
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
        quarter-finalists. The biggest misses were Uruguay, out in the groups with an 89% chance of going through,
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
        charts.append(styled((reference + line).properties(width="container", height=230, title=name)))
    return charts


def styled(chart):
    return (
        chart.configure(font="Barlow, Helvetica, Arial, sans-serif")
        .configure_title(font="Barlow Condensed, Arial Narrow, sans-serif", fontSize=17, fontWeight=600, color=INK, anchor="start")
        .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#E4E7EC", domainColor="#C3C8D0", labelFontSize=12)
        .configure_legend(labelColor=INK, labelFontSize=13, title=None, orient="top", symbolStrokeWidth=3)
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
    for column, chart in zip(st.columns(3, gap="medium"), calibration_chart(data["calibration"])):
        with column:
            st.altair_chart(chart, theme=None)


def outcome_probs(predictions, model):
    return predictions[[f"{model}_{o}" for o in OUTCOMES]].to_numpy()


def match_log_loss(predictions, model):
    actual = predictions["result"].map(OUTCOMES.index).to_numpy()
    p_true = outcome_probs(predictions, model)[np.arange(len(actual)), actual]
    return -np.log(np.clip(p_true, 1e-15, 1))


def predicted_outcome(predictions, model):
    return np.array(OUTCOMES)[outcome_probs(predictions, model).argmax(axis=1)]


def score_table(scores, predictions):
    table = scores.set_index("model")[["log_loss", "brier", "rps"]].copy()
    table["accuracy"] = [
        1 / 3 if model == "uniform" else np.mean(predicted_outcome(predictions, model) == predictions["result"])
        for model in table.index
    ]
    return table


def metric_chart(table):
    names = {"log_loss": "Log loss", "brier": "Brier score", "rps": "Ranked probability score"}
    long = (
        table[list(names)].rename_axis("model").reset_index()
        .melt(id_vars="model", var_name="metric", value_name="value")
        .assign(label=lambda d: d["model"].map(MODEL_LABELS), final=lambda d: d["model"] == "poisson")
    )
    order = list(MODEL_LABELS.values())
    charts = []
    for metric, title in names.items():
        base = alt.Chart(long[long["metric"] == metric])
        y_axis = alt.Axis(title=None, labelFontSize=13, labelColor=INK)
        dots = base.mark_circle(size=140, opacity=1).encode(
            x=alt.X("value:Q", title=None, scale=alt.Scale(zero=False, padding=16)),
            y=alt.Y("label:N", sort=order, axis=y_axis),
            color=alt.condition("datum.final", alt.value(ACCENT), alt.value("#9AA1AD")),
            tooltip=[alt.Tooltip("label:N", title="Model"), alt.Tooltip("value:Q", format=".4f", title=title)],
        )
        values = base.mark_text(dy=-13, fontSize=12, color=MUTED).encode(
            x="value:Q", y=alt.Y("label:N", sort=order), text=alt.Text("value:Q", format=".3f")
        )
        charts.append(styled((dots + values).properties(width="container", height=220, title=title)))
    return charts


def quarterly_chart(predictions):
    quarters = predictions["date"].dt.to_period("Q").astype(str).str.replace("Q", " Q")
    frames = [
        pd.DataFrame({"quarter": quarters, "model": MODEL_LABELS[m], "log_loss": match_log_loss(predictions, m)})
        for m in ["elo_logistic", "poisson"]
    ]
    data = pd.concat(frames).groupby(["quarter", "model"], as_index=False).agg(
        log_loss=("log_loss", "mean"), games=("log_loss", "size")
    )
    return styled(
        alt.Chart(data)
        .mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=55, filled=True))
        .encode(
            x=alt.X("quarter:O", title=None, axis=alt.Axis(labelAngle=0, labelFontSize=11)),
            y=alt.Y("log_loss:Q", title="Log loss", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "model:N",
                scale=alt.Scale(domain=["Elo rating", "Goal model"], range=["#9AA1AD", ACCENT]),
            ),
            tooltip=["quarter:O", "model:N", alt.Tooltip("log_loss:Q", format=".3f", title="Log loss"), "games:Q"],
        )
        .properties(width="container", height=260)
    )


def cumulative_chart(predictions):
    gain = match_log_loss(predictions, "elo_logistic") - match_log_loss(predictions, "poisson")
    n = np.arange(1, len(gain) + 1)
    noise = 2 * gain.std(ddof=1) * np.sqrt(n)
    data = pd.DataFrame({"game": n, "gain": gain.cumsum(), "low": -noise, "high": noise})
    band = alt.Chart(data).mark_area(color="#E4E7EC").encode(
        x=alt.X("game:Q", title="Test games, in date order", scale=alt.Scale(domain=[0, len(gain)], nice=False)),
        y=alt.Y("low:Q", title="Log loss saved over Elo"),
        y2="high:Q",
    )
    line = alt.Chart(data).mark_line(color=ACCENT, strokeWidth=2.5).encode(
        x="game:Q", y="gain:Q", tooltip=[alt.Tooltip("game:Q", title="Games"), alt.Tooltip("gain:Q", format=".1f", title="Saved")]
    )
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#9AA1AD").encode(y="y:Q")
    return styled((band + zero + line).properties(width="container", height=260))


def confusion_table(predictions, model):
    predicted = predicted_outcome(predictions, model)
    actual = predictions["result"].to_numpy()
    counts = pd.crosstab(pd.Categorical(actual, OUTCOMES), pd.Categorical(predicted, OUTCOMES), dropna=False)
    counts = counts.reindex(index=OUTCOMES, columns=OUTCOMES, fill_value=0)
    header = "".join(f"<th>{OUTCOME_LABELS[o]}</th>" for o in OUTCOMES)
    rows = ""
    for o in OUTCOMES:
        share = counts.loc[o] / counts.loc[o].sum()
        cells = ""
        for c in OUTCOMES:
            alpha = min(1.0, share[c] ** 0.75)
            color = "#FFFFFF" if alpha > 0.55 else INK
            cells += f'<td style="background: rgba(29, 91, 214, {alpha:.3f}); color: {color};">{counts.loc[o, c]:,}</td>'
        rows += f'<tr><td class="team">{OUTCOME_LABELS[o]}</td>{cells}<td class="side">{share[o]:.0%}</td></tr>'
    precision = "".join(
        f'<td class="side">{counts.loc[c, c] / counts[c].sum():.0%}</td>' if counts[c].sum() else '<td class="side">n/a</td>'
        for c in OUTCOMES
    )
    return (
        f'<table class="confusion"><tr><th></th>{header}<th>Recall</th></tr>{rows}'
        f'<tr><td class="team">Precision</td>{precision}<td></td></tr></table>'
    )


def plain_table(header, rows):
    head = "".join(f"<th>{h}</th>" for h in header)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<table class="plain"><tr>{head}</tr>{body}</table>'


def section(title, text):
    st.markdown(f'<div class="group-title">{title}</div><p class="lede">{text}</p>', unsafe_allow_html=True)


def scores_tab(data):
    predictions = data["predictions"]
    table = score_table(data["scores"], predictions)
    gain = match_log_loss(predictions, "elo_logistic") - match_log_loss(predictions, "poisson")
    std_error = gain.std(ddof=1) / np.sqrt(len(gain))
    st.markdown(
        f'<p class="lede">The same {len(predictions):,} test games, scored with the usual metrics for probability '
        f'forecasts. Each one compares the announced probabilities with the result that happened. '
        f'Lower is better.</p>',
        unsafe_allow_html=True,
    )
    for column, chart in zip(st.columns(3, gap="medium"), metric_chart(table)):
        with column:
            st.altair_chart(chart, theme=None)
    rows = [
        [MODEL_LABELS[m], f"{r.log_loss:.4f}", f"{r.brier:.4f}", f"{r.rps:.4f}", f"{r.accuracy:.1%}"]
        for m, r in table.loc[list(MODEL_LABELS)].iterrows()
    ]
    st.markdown(plain_table(["Model", "Log loss", "Brier", "RPS", "Accuracy"], rows), unsafe_allow_html=True)
    st.markdown(
        '<p class="note"><b>Log loss</b>: minus the log of the probability given to the actual result. '
        'It punishes confident mistakes hardest. <b>Brier</b>: squared distance between the three probabilities and '
        'the result coded as 0 or 1. <b>RPS</b>: the same on cumulative probabilities, so calling a draw when the home '
        'side wins costs less than calling an away win. <b>Accuracy</b>: how often the most likely result happened. '
        'I show it for reference only, since it ignores how confident the forecast was.</p>',
        unsafe_allow_html=True,
    )

    section(
        "Is the gain over Elo real?",
        f"The goal model saves {gain.mean():.3f} log loss per game over the Elo rating, with a standard error of "
        f"{std_error:.4f}. The blue line adds up the gain game after game. The grey band is how far the sum could "
        f"drift by chance alone (two standard deviations). The line leaves the band early and keeps climbing.",
    )
    st.altair_chart(cumulative_chart(predictions), theme=None)

    section(
        "Is it stable over time?",
        "Log loss by quarter. The level moves with the calendar, since friendlies and qualifiers are not equally "
        "predictable. The goal model is never behind the Elo rating: clearly ahead in most quarters, level in the others.",
    )
    st.altair_chart(quarterly_chart(predictions), theme=None)

    section(
        "Which results does it get wrong?",
        "If I keep only the most likely result for each game, I get this confusion matrix for the goal model. "
        "Rows are what happened, columns the most likely result. Shading is the share of each row.",
    )
    st.markdown(confusion_table(predictions, "poisson"), unsafe_allow_html=True)
    st.markdown(
        '<p class="note">A draw is almost never the single most likely result, even when its probability is close '
        'to 30%, so draw recall is near zero. This is expected for a three-way forecast and is the reason I judge '
        'the model on its probabilities rather than on accuracy.</p>',
        unsafe_allow_html=True,
    )

    section(
        "What each model is trained to minimise",
        "The training loss and the evaluation metric are not always the same thing.",
    )
    st.markdown(
        plain_table(
            ["Model", "Predicts", "Training loss"],
            [
                ["Elo rating", "Result", "Multinomial cross-entropy on the Elo gap and home advantage"],
                ["Gradient boosting", "Result", "Multinomial cross-entropy on pre-match features"],
                ["Goal model", "Goals of each team", "Poisson negative log-likelihood, weighted by recency, small L2 penalty"],
            ],
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="note">The goal model never sees win, draw or loss during training. It learns to predict goals, '
        'and the result probabilities come from the score distribution. It still scores best on the result metrics.</p>',
        unsafe_allow_html=True,
    )


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
    nations, world_cup, reliability, scores, method = st.tabs(
        ["Nations League", "World Cup 2026", "Reliability", "Scores", "Method"]
    )
    with nations:
        nations_league_tab(data)
    with world_cup:
        world_cup_tab(data)
    with reliability:
        reliability_tab(data)
    with scores:
        scores_tab(data)
    with method:
        method_tab()


main()
