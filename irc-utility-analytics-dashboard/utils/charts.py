from __future__ import annotations
import plotly.express as px
import plotly.graph_objects as go

STATE_ABBR = {
'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'
}

def line(df, x, y, title, color=None):
    fig = px.line(df, x=x, y=y, markers=True, title=title, color=color)
    fig.update_layout(height=300, margin=dict(l=10,r=10,t=45,b=10), plot_bgcolor='white', paper_bgcolor='white')
    return fig

def scatter(df, x, y, title, color=None, hover_name=None):
    fig = px.scatter(df, x=x, y=y, color=color, hover_name=hover_name, title=title)
    fig.update_layout(height=300, margin=dict(l=10,r=10,t=45,b=10), plot_bgcolor='white', paper_bgcolor='white')
    return fig

def bar(df, x, y, title, color=None):
    fig = px.bar(df, x=x, y=y, color=color, title=title)
    fig.update_layout(height=330, margin=dict(l=10,r=10,t=45,b=10), plot_bgcolor='white', paper_bgcolor='white')
    return fig

def state_choropleth(df, metric="Cost_per_Treatment"):
    state = df.groupby('State', as_index=False).agg(**{metric:(metric,'mean')}, Centers=('Property Name','nunique'))
    fig = px.choropleth(state, locations='State', locationmode='USA-states', color=metric, scope='usa', hover_data=['Centers'], title=f'{metric.replace("_", " ")} by State')
    fig.update_layout(height=520, margin=dict(l=0,r=0,t=40,b=0), geo=dict(bgcolor='rgba(0,0,0,0)'))
    return fig
