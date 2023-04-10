from email import header
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode, ColumnsAutoSizeMode, DataReturnMode
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

custom_css = {
".ag-root.ag-unselectable.ag-layout-normal": {"font-size": "15px !important",
"font-family": "Roboto, sans-serif !important;"},
".ag-header-cell-text": {"color": "#495057 !important;"},
".ag-theme-alpine .ag-ltr .ag-cell": {"color": "#444 !important;"},
".ag-theme-alpine .ag-row-odd": {"background": "rgba(243, 247, 249, 0.3) !important;",
"border": "1px solid #eee !important;"},
".ag-theme-alpine .ag-row-even": {"border-bottom": "1px solid #eee !important;"},
".ag-theme-light button": {"font-size": "0 !important;", "width": "auto !important;", "height": "24px !important;",
"border": "1px solid #eee !important;", "margin": "4px 2px !important;",
"background": "#3162bd !important;", "color": "#fff !important;",
"border-radius": "3px !important;"},
".ag-theme-light button:before": {"content": "'Confirm' !important", "position": "relative !important",
"z-index": "1000 !important", "top": "0 !important",
"font-size": "10px !important", "left": "0 !important",
"padding": "4px !important"},
}


def aggrid_interactive_table_session(df: pd.DataFrame):
    """Creates an st-aggrid interactive table based on a dataframe.

    Args:
        df (pd.DataFrame]): Source dataframe

    Returns:
        dict: The selected row
    """
    options = GridOptionsBuilder.from_dataframe(
        df, enableRowGroup=True, enableValue=True, enablePivot=True,
    )

    options.configure_side_bar()
    options.configure_selection(selection_mode="multiple")# , use_checkbox=True, header_checkbox=True)
    options.configure_column(field="session", sort="asc")
    options.configure_column(field="h2o", hide=True, rowGroup=True)
    options.configure_column(field='subject_id', hide=True)
    options.configure_column(field="session_date", type=["customDateTimeFormat"], custom_format_string='yyyy-MM-dd')
    options.configure_column(field="ephys_ins", dateType="DateType")
    
    # options.configure_column(field="water_restriction_number", header_name="subject", 
    #                          children=[dict(field="water_restriction_number", rowGroup=True),
    #                                    dict(field="session")])
    
    selection = AgGrid(
        df,
        enable_enterprise_modules=True,
        gridOptions=options.build(),
        theme="balham",
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        height=500,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        custom_css=custom_css,
    )

    return selection

def aggrid_interactive_table_units(df: pd.DataFrame, height=500):
    """Creates an st-aggrid interactive table based on a dataframe.

    Args:
        df (pd.DataFrame]): Source dataframe

    Returns:
        dict: The selected row
    """
    options = GridOptionsBuilder.from_dataframe(
        df, enableRowGroup=True, enableValue=True, enablePivot=True,
    )

    options.configure_selection(selection_mode="multiple", use_checkbox=False, header_checkbox=True)
    options.configure_side_bar()
    options.configure_selection("single")
    options.configure_columns(column_names=['subject_id', 'electrode'], hide=True)
 

    # options.configure_column(field="water_restriction_number", header_name="subject", 
    #                          children=[dict(field="water_restriction_number", rowGroup=True),
    #                                    dict(field="session")])
    
    selection = AgGrid(
        df,
        enable_enterprise_modules=True,
        gridOptions=options.build(),
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        theme="balham",
        update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.FILTERING_CHANGED,
        allow_unsafe_jscode=True,
        height=height,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        custom_css=custom_css,
    )

    return selection

def cache_widget(field, clear=None):
    st.session_state[f'{field}_cache'] = st.session_state[field]
    
    # Clear cache if needed
    if clear:
        if clear in st.session_state: del st.session_state[clear]
        
# def dec_cache_widget_state(widget, ):


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    
    # modify = st.checkbox("Add filters")

    # if not modify:
    #     return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()
    
    with modification_container:
        st.markdown(f"Add filters")
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns,
                                                            label_visibility='collapsed',
                                                            default=st.session_state.to_filter_columns_cache 
                                                                    if 'to_filter_columns_cache' in st.session_state
                                                                    else ['area_of_interest'],
                                                            key='to_filter_columns',
                                                            on_change=cache_widget,
                                                            args=['to_filter_columns'])
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 30:
                right.markdown(f"Filter for **{column}**")
                selected = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    label_visibility='collapsed',
                    default=st.session_state[f'select_{column}_cache']
                            if f'select_{column}_cache' in st.session_state
                            else list(df[column].unique()),
                    key=f'select_{column}',
                    on_change=cache_widget,
                    args=[f'select_{column}']
                )
                df = df[df[column].isin(selected)]
                
            elif is_numeric_dtype(df[column]):
                
                # fig = px.histogram(df[column], nbins=100, )
                # fig.update_layout(showlegend=False, height=50)
                # st.plotly_chart(fig)
                # counts, bins = np.histogram(df[column], bins=100)
                # st.bar_chart(pd.DataFrame(
                #                 {'x': bins[1:], 'y': counts},
                #                 ),
                #                 x='x', y='y')
                
                with right:
                    col1, col2 = st.columns((3, 1))
                    col1.markdown(f"Filter for **{column}**")
                    if float(df[column].min()) >= 0: 
                        show_log = col2.checkbox('log 10', 
                                                 value=st.session_state[f'if_log_{column}_cache']
                                                       if f'if_log_{column}_cache' in st.session_state
                                                       else False,
                                                 key=f'if_log_{column}',
                                                 on_change=cache_widget,
                                                 args=[f'if_log_{column}'],
                                                 kwargs={'clear': f'select_{column}_cache'}  # If show_log is changed, clear select cache
                                                 )
                    else:
                        show_log = 0
                        
                    if show_log:
                        x = np.log10(df[column] + 1e-6)  # Cutoff at 1e-5
                    else:
                        x = df[column]               
                        
                    _min = float(x.min())
                    _max = float(x.max())
                    step = (_max - _min) / 100

                    c_hist = st.container()  # Histogram
                    
                    user_num_input = st.slider(
                        f"Values for {column}",
                        label_visibility='collapsed',
                        min_value=_min,
                        max_value=_max,
                        value= st.session_state[f'select_{column}_cache']
                                if f'select_{column}_cache' in st.session_state
                                else (_min, _max),
                        step=step,
                        key=f'select_{column}',
                        on_change=cache_widget,
                        args=[f'select_{column}']
                    )
                    
                    with c_hist:
                        
                        counts, bins = np.histogram(x, bins=100)
                        
                        fig = px.bar(x=bins[1:], y=counts)
                        fig.add_vrect(x0=user_num_input[0], x1=user_num_input[1], fillcolor='red', opacity=0.1, line_width=0)
                        fig.update_layout(showlegend=False, height=100, 
                                          yaxis=dict(visible=False),
                                          xaxis=dict(title=f'log 10 ({column})' if show_log else column,
                                                     range=(_min, _max)),
                                          margin=dict(l=0, r=0, t=0, b=0))
                        st.plotly_chart(fig, use_container_width=True)

                    df = df[x.between(*user_num_input)]
                
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df


from datetime import datetime 

import s3fs
from PIL import Image, ImageColor

cache_fig_drift_metrics_folder = 'aind-behavior-data/Han/ephys/report/unit_drift_metrics/'
cache_fig_psth_folder = 'aind-behavior-data/Han/ephys/report/all_units/'
fs = s3fs.S3FileSystem(anon=False)



def add_unit_filter():
    with st.expander("Unit filter", expanded=True):   
        st.session_state.df_unit_filtered = filter_dataframe(df=st.session_state.df['df_ephys_units'])
        # Join with df_period_linear_fit_all here! (A huge dataframe with all things merged (flattened multi-level columns)
        st.session_state.df_unit_filtered_merged = st.session_state.df_unit_filtered.set_index(st.session_state.unit_key_names + ['area_of_interest']
                                                                                        ).join(st.session_state.df['df_period_linear_fit_all'], how='inner')
        
        n_units = len(st.session_state.df_unit_filtered)
        n_animal = len(st.session_state.df_unit_filtered['subject_id'].unique())
        n_insertion = len(st.session_state.df_unit_filtered.groupby(['subject_id', 'session', 'insertion_number']))
        st.markdown(f'#### {n_units} units, {n_animal} mice, {n_insertion} insertions')

def add_unit_selector():
    with st.expander(f'Unit selector', expanded=True):
        
        n_units = len(st.session_state.df_unit_filtered)
                        
        with st.expander(f"Filtered: {n_units} units", expanded=False):
            st.dataframe(st.session_state.df_unit_filtered)
        
        for i, source in enumerate(st.session_state.select_sources):
            df_selected_this = st.session_state[f'df_selected_from_{source}']
            cols = st.columns([4, 1])
            with cols[0].expander(f"Selected: {len(df_selected_this)} units from {source}", expanded=False):
                st.dataframe(df_selected_this)
                
            if cols[1].button('❌' + ' '*i):  # Avoid duplicat key
                st.session_state[f'df_selected_from_{source}'] = pd.DataFrame(columns=[st.session_state.unit_key_names])
                st.experimental_rerun()
        

def unit_plot_settings(default_source='xy_view', need_click=True):
    
    cols = st.columns([3, 1])
    
    st.session_state.unit_select_source = cols[0].selectbox('Which unit(s) to draw?', 
                                            [f'selected from {source} '
                                             f'({len(st.session_state[f"df_selected_from_{source}"])} units)' 
                                             for source in st.session_state.select_sources], 
                                            index=st.session_state.select_sources.index(default_source)
                                            )
        
    # cols[0].markdown(f'##### Show selected {len(df_selected)} unit(s)')
    st.session_state.num_cols = cols[1].number_input('Number of columns', 1, 10, 
                                                     st.session_state.num_cols if 'num_cols' in st.session_state else 3)

    st.session_state.draw_types = st.multiselect('Which plot(s) to draw?', ['psth', 'drift metrics'], 
                                                 default=st.session_state.draw_types if 'draw_types' in st.session_state else ['psth'])
    
    if need_click:
        cols = st.columns([1, 3])
        auto_draw = cols[0].checkbox('Auto draw', value=False)
        draw_it = cols[1].button(f'================ 🎨 Draw! ================', use_container_width=True)
    else:
        draw_it = True
    return draw_it or auto_draw



@st.cache_data(max_entries=100)
def get_fig_unit_psth_only(key):
    fn = f'*{key["h2o"]}_{key["session_date"]}_{key["insertion_number"]}*u{key["unit"]:03}*'
    aoi = key["area_of_interest"]
    
    file = fs.glob(cache_fig_psth_folder + ('' if aoi == 'others' else aoi + '/') + fn)
    if len(file) == 1:
        with fs.open(file[0]) as f:
            img = Image.open(f)
            img = img.crop((500, 140, 3000, 2800)) 
    else:
        img = None
            
    return img

@st.cache_data(max_entries=100)
def get_fig_unit_drift_metric(key):
    fn = f'*{key["subject_id"]}_{key["session"]}_{key["insertion_number"]}_{key["unit"]:03}*'
    
    file = fs.glob(cache_fig_drift_metrics_folder + fn)
    if len(file) == 1:
        with fs.open(file[0]) as f:
            img = Image.open(f)
            img = img.crop((0, 0, img.size[0], img.size[1]))  
    else:
        img = None
            
    return img

draw_func_mapping = {'psth': get_fig_unit_psth_only,
                     'drift metrics': get_fig_unit_drift_metric}


def draw_selected_units():    
    
    for source in st.session_state.select_sources:
        if source in st.session_state.unit_select_source: break
        
    df_selected = st.session_state[f'df_selected_from_{source}']
    
    st.write(f'Loading selected {len(df_selected)} units...')
    my_bar = st.columns((1, 7))[0].progress(0)

    cols = st.columns([1]*st.session_state.num_cols)
    
    for i, key in enumerate(df_selected.reset_index().to_dict(orient='records')):
        key['session_date'] = datetime.strftime(datetime.strptime(str(key['session_date']), '%Y-%m-%d %H:%M:%S'), '%Y%m%d')
        col = cols[i%st.session_state.num_cols]
        col.markdown(f'''<h5 style='text-align: center; color: orange;'>{key["h2o"]}, ''' 
            f'''Session {key["session"]}, {key['session_date']}, unit {key["unit"]} ({key["area_of_interest"]})</h3>''',
            unsafe_allow_html=True)

        for draw_type in st.session_state.draw_types:
            img = draw_func_mapping[draw_type](key)
            if img is None:
                col.markdown(f'{draw_type} fetch error')
            else:
                col.image(img, output_format='PNG', use_column_width=True)
        
        col.markdown("---")
        my_bar.progress(int((i + 1) / len(df_selected) * 100))