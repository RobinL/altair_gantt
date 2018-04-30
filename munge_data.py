import pandas as pd
import altair as alt

CHART_WIDTH = 700

def resample_and_add_zeros(df):
    task_id = df.iloc[0,0]
    data = {"task_id" : [task_id], "num_fte": [0], "weeks_work":[0]}
    before = pd.DataFrame(data, index = [df.index[0] - pd.DateOffset(1)])
    after = pd.DataFrame(data, index = [df.index[1] + pd.DateOffset(1)])
    df = pd.concat([before,df,after])
    return df.resample('D').fillna(method='pad')


gd = pd.read_csv("gantt.csv", parse_dates=["start", "end"])
gd["end"] = gd["end"] - pd.DateOffset(1)
gd["num_fte"] = gd["weeks_work"]*7/(gd["end"] - gd["start"]).dt.days
gd['task_id'] = range(1, len(gd)+1)
gd["task"] = gd['task_id'].map('{:02}'.format) + " " +  gd["task"]
starts = gd[['start', 'task_id']].rename(columns={'start': 'date'})
ends = gd[['end', 'task_id']].rename(columns={'end': 'date'})
start_end = pd.concat([starts, ends]).set_index('date')


cols_retain =['start', 'task_id', "num_fte", "weeks_work"]
starts = gd[cols_retain].rename(columns={'start': 'date'})

cols_retain =['end', 'task_id', "num_fte", "weeks_work"]
ends = gd[cols_retain].rename(columns={'end': 'date'})
start_end = pd.concat([starts, ends]).set_index('date')

fact_table = start_end.groupby("task_id").apply(resample_and_add_zeros)
del fact_table["task_id"]
fact_table = fact_table.reset_index()
fact_table = fact_table.rename(columns={'level_1':'date'})

merge_gd = gd.copy()
del merge_gd["weeks_work"]
del merge_gd["num_fte"]

final = fact_table.merge(merge_gd, right_on='task_id', left_on='task_id', how='left')

f1 = final["date"].dt.day % 5 == 0
final = final[f1]

dead = pd.read_csv("deadlines.csv")

# Set up common x axis
dt1 = alt.DateTime(year=2018, month=4)
dt2 = alt.DateTime(year=2019, month=10)
x_scale=alt.Scale(domain=(dt1,dt2))
tt = [{"field": "person"}, {"field":"num_fte", "format": ".2f"}]
no_axis_title = axis=alt.Axis(title="")

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
                x=alt.X('start', scale=x_scale, axis=no_axis_title),
                x2='end',
                y=alt.Y('task', scale=y_scale, axis=no_axis_title),
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
    x=alt.X('date', scale=x_scale, axis=no_axis_title),
    y= alt.Y('sum(num_fte)', axis=alt.Axis(title="Sum of FTE required")),
    color='person'
).properties(width = CHART_WIDTH, height = 100)

alt_cat = alt_util.mark_line().encode(
    y= alt.Y('sum(num_fte)', axis=alt.Axis(title="FTE required")),
    color='category'
)
import numpy as np
gd['priority'] = gd['priority'] + np.random.uniform(-1, 1, len(gd))
gd['weeks_work'] = gd['weeks_work'] + np.random.uniform(-1, 1, len(gd))

alt_work = alt.Chart(gd).mark_point().encode(
 x = alt.X('weeks_work', axis=alt.Axis(title="Weeks of work for task")),
 y = alt.X('priority', axis=alt.Axis(title="Task value/priority")),
 tooltip='desc',
 color=alt.Color('person', legend=False)
).properties(width = CHART_WIDTH, height=500)

alt_work_text = alt_work.mark_text(align="left", baseline="middle", size=10, dx=5, dy=-5).encode(
 text= 'task'
)

alt_work_layered = alt_work + alt_work_text

vconcat = alt.vconcat(alt_gantt_layered, alt_util, alt_cat).resolve_scale("independent")

final_chart = alt.hconcat(vconcat, alt_work_layered)
final_chart.savechart("index.html", validate=False)
