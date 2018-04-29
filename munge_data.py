import pandas as pd
import altair as alt
from datetime import datetime


CHART_WIDTH = 500
START_YEAR = 2018
START_MONTH = 1

END_YEAR = 2020
END_MONTH = 1

gd = pd.read_csv("gantt.csv", parse_dates=["start", "end"])
gd["end"] = gd["end"] - pd.DateOffset(1)
gd["num_fte"] = gd["weeks_work"]*7/(gd["end"] - gd["start"]).dt.days
gd['task_id'] = range(1, len(gd)+1)
gd["task"] = gd['task_id'].map('{:02}'.format) + " " +  gd["task"]
starts = gd[['start', 'task_id']].rename(columns={'start': 'date'})
ends = gd[['end', 'task_id']].rename(columns={'end': 'date'})
start_end = pd.concat([starts, ends]).set_index('date')

fact_table = start_end.groupby("task_id").apply(lambda x: x.resample('D').fillna(method='pad'))
del fact_table["task_id"]
fact_table = fact_table.reset_index()
final = fact_table.merge(gd, right_on='task_id', left_on='task_id', how='left')

f1 = final["date"].dt.day == 1
f2 = final["date"].dt.day == 16
final = final[f1 | f2]

dead = pd.read_csv("deadlines.csv")

# Set up common x axis
dt1 = alt.DateTime(year=START_YEAR, month=START_MONTH)
dt2 = alt.DateTime(year=END_YEAR, month=END_MONTH)
x_scale=alt.Scale(domain=(dt1,dt2))
tt = [{"field": "person"}, {"field":"num_fte", "format": ".2f"}]

alt_dead = alt.Chart(dead).mark_text(align="center", baseline="middle", size=20).encode(
    y = alt.Y('task_o:N'),
    x = alt.X('start:T', scale=x_scale),
    text = alt.Text('mark')
)

alt_dead.encoding.tooltip = [{"field": "dead_desc"}]

y_scale = alt.Scale(padding=0.3)

alt_gantt_1 = alt.\
            Chart(gd).\
            mark_bar().\
            encode(
                x=alt.X('start', scale=x_scale),
                x2='end',
                y=alt.Y('task', scale=y_scale),
                color=alt.Color('person', legend=alt.Legend(orient="right")),
                opacity = alt.Opacity('num_fte', legend=False)
            )\
            .properties(width = CHART_WIDTH)

alt_gantt_1.encoding.tooltip = tt

alt_gantt_2 =  alt_gantt_1.mark_text(dx=4, dy=0, align='left', baseline='middle')\
    .encode(
    text='desc'
    )
alt_gantt_2.encoding.color = alt.Undefined
alt_gantt_2.encoding.opacity = alt.Undefined
alt_gantt_2.encoding.tooltip = tt

alt_gantt_layered = alt.LayerChart([alt_gantt_1, alt_gantt_2, alt_dead])

alt_util = alt.Chart(final).mark_area(interpolate="monotone").encode(
    x=alt.X('date', scale=x_scale),
    y='sum(num_fte)',
    color='person'
).properties(width = CHART_WIDTH, height = 100)

alt_cat = alt_util.mark_line().encode(
    y='sum(num_fte)',
    color='category'
)

final = alt.vconcat(alt_gantt_layered, alt_util, alt_cat).resolve_scale("independent")

final.savechart("index.html", validate=False)
