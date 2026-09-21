import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# 0. 앱 설정과 공통 문구
# ============================================================
TITLE = '영화 데이터 그래프 도감 1 - 시간'
DATA_URL = 'https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv'
# 그래프 아래에 표시할 한 문장을 이곳에서 수정하세요.
GRAPH_1_INSIGHT = '선택한 영화의 일관객이 시간에 따라 언제 늘고 줄었는지 알 수 있습니다.'

GRAPH_2_INSIGHT = '기간 내 일관객 합계가 큰 5편의 관객수 변화와 흥행이 집중된 시기를 비교할 수 있습니다.'

GRAPH_3_INSIGHT = '날짜별 10위권 관객 규모의 변화와 관객이 가장 많이 몰린 3일을 알 수 있습니다.'

GRAPH_4_INSIGHT = '기간 내 일관객 합계가 큰 영화 10편의 관객 규모와 10위권에 머문 날수를 비교할 수 있습니다.'

GRAPH_5_INSIGHT = '어느 월과 요일 조합에 10위권 관객이 많이 모였는지 색의 진하기로 비교할 수 있습니다.'

st.set_page_config(page_title=TITLE, page_icon='🎬', layout='wide')

# ============================================================
# 1. 데이터 불러오기 및 전처리
# ============================================================
@st.cache_data(ttl=3600)
def load_data(url):
    df = pd.read_csv(url, encoding='utf-8-sig', dtype={'날짜': str, '영화코드': str})
    required = ['날짜', '순위', '영화코드', '영화명', '일관객', '누적관객', '스크린수', '상영횟수']
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f'필수 열이 없습니다: {", ".join(sorted(missing))}')
    # 20250901 같은 여덟 자리 날짜를 실제 datetime으로 변환합니다.
    df['날짜'] = pd.to_datetime(df['날짜'].str.strip(), format='%Y%m%d', errors='raise')
    for col in ['순위', '일관객', '누적관객', '스크린수', '상영횟수']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '', regex=False), errors='raise')
    return df.sort_values(['날짜', '순위']).reset_index(drop=True)


def show_insight(sentence):
    st.markdown(f'**이 그래프로 알 수 있는 것:** {sentence}')

# ============================================================
# 2. 그래프 1 — 영화별 날짜에 따른 일관객 변화
# ============================================================
def show_daily_audience(df):
    st.header('1. 영화별 일관객 변화')
    movies = df[['영화코드', '영화명']].drop_duplicates('영화코드').sort_values('영화명')
    names = movies.set_index('영화코드')['영화명'].to_dict()
    duplicate_names = set(movies.loc[movies['영화명'].duplicated(keep=False), '영화명'])
    selected = st.selectbox(
        '영화를 선택하세요',
        options=movies['영화코드'].tolist(),
        format_func=lambda code: f'{names[code]} ({code})' if names[code] in duplicate_names else names[code],
        key='graph_1_movie',
    )
    movie = df.loc[df['영화코드'] == selected].sort_values('날짜')
    # 10위권 밖의 날짜는 관객수 0이 아닙니다. 결측값으로 선을 끊습니다.
    dates = pd.date_range(movie['날짜'].min(), movie['날짜'].max(), freq='D')
    series = movie.set_index('날짜')['일관객'].reindex(dates)
    plot_data = series.rename_axis('날짜').reset_index()
    fig = px.line(
        plot_data, x='날짜', y='일관객', markers=True,
        title=f'{names[selected]} — 날짜별 일관객',
        labels={'날짜': '날짜', '일관객': '일관객 (명)'},
    )
    fig.update_traces(
        connectgaps=False,
        hovertemplate='날짜: %{x|%Y-%m-%d}<br>관객수: %{y:,.0f}명<extra></extra>',
    )
    fig.update_layout(hovermode='closest', xaxis_title='날짜', yaxis_title='일관객 (명)')
    fig.update_xaxes(tickformat='%Y-%m-%d')
    fig.update_yaxes(tickformat=',.0f', rangemode='tozero')
    st.plotly_chart(fig, use_container_width=True)
    show_insight(GRAPH_1_INSIGHT)
    st.caption('일별 박스오피스 10위권에 포함된 기록만 표시합니다. 기록이 없는 날짜는 관객수 0을 뜻하지 않으며, 선을 연결하지 않습니다.')

# ============================================================
# 3. 그래프 2 — 기간 내 일관객 합계 상위 5편 비교
# ============================================================
def show_top_five(df):
    st.header('2. 일관객 합계 상위 5편 비교')
    # 누적관객이 아니라, 데이터 기간에 기록된 일관객을 합산합니다.
    top_codes = df.groupby('영화코드')['일관객'].sum().nlargest(5).index.tolist()
    names = df.drop_duplicates('영화코드').set_index('영화코드')['영화명']
    top_names = names.loc[top_codes]
    duplicates = set(top_names[top_names.duplicated(keep=False)])
    dates = pd.date_range(df['날짜'].min(), df['날짜'].max(), freq='D')
    parts = []
    labels = []
    for code in top_codes:
        label = f'{names[code]} ({code})' if names[code] in duplicates else names[code]
        labels.append(label)
        daily = df.loc[df['영화코드'] == code].groupby('날짜')['일관객'].sum()
        part = daily.reindex(dates).rename_axis('날짜').reset_index()
        part['영화'] = label
        parts.append(part)
    plot_data = pd.concat(parts, ignore_index=True)
    fig = px.line(
        plot_data, x='날짜', y='일관객', color='영화',
        category_orders={'영화': labels},
        color_discrete_sequence=px.colors.qualitative.Safe,
        labels={'날짜': '날짜', '일관객': '일관객 (명)'},
        custom_data=['영화'],
    )
    fig.update_traces(
        connectgaps=False,
        hovertemplate='영화: %{customdata[0]}<br>날짜: %{x|%Y-%m-%d}<br>관객수: %{y:,.0f}명<extra></extra>',
    )
    fig.update_layout(
        hovermode='closest',
        legend={'title_text': '영화 (클릭하여 켜기·끄기)',
                'itemclick': 'toggle', 'itemdoubleclick': 'toggleothers'},
    )
    fig.update_xaxes(tickformat='%Y-%m-%d')
    fig.update_yaxes(tickformat=',.0f', rangemode='tozero')
    st.plotly_chart(fig, use_container_width=True, key='graph_2_top_five')
    show_insight(GRAPH_2_INSIGHT)
    st.caption('범례를 클릭하면 해당 영화를 숨기거나 다시 표시하며, 두 번 클릭하면 그 영화만 볼 수 있습니다.')
    st.caption('상위 5편은 이 데이터에 포함된 10위권 기록의 일관객 합계로 선정합니다. 기록이 없는 날짜는 0으로 채우지 않고 선을 끊습니다.')

# ============================================================
# 4. 그래프 3 — 날짜별 10위권 일관객 합계
# ============================================================
def show_daily_total(df):
    st.header('3. 날짜별 10위권 일관객 합계')
    daily = (
        df.loc[df['순위'].between(1, 10)]
        .groupby('날짜', as_index=False)['일관객'].sum()
        .rename(columns={'일관객': '일관객 합계'})
        .sort_values('날짜')
    )
    if daily.empty:
        st.info('표시할 10위권 기록이 없습니다.')
        return
    # 동률이면 날짜가 이른 날을 먼저 선택합니다.
    top_days = daily.sort_values(
        ['일관객 합계', '날짜'], ascending=[False, True]
    ).head(3)
    fig = px.area(
        daily, x='날짜', y='일관객 합계',
        labels={'날짜': '날짜', '일관객 합계': '10위권 일관객 합계 (명)'},
        color_discrete_sequence=['#4682B4'],
    )
    fig.update_traces(
        hovertemplate='날짜: %{x|%Y-%m-%d}<br>10위권 일관객 합계: %{y:,.0f}명<extra></extra>'
    )
    fig.add_scatter(
        x=top_days['날짜'], y=top_days['일관객 합계'], mode='markers',
        marker={'size': 10, 'color': '#D94841'}, showlegend=False,
        hovertemplate='날짜: %{x|%Y-%m-%d}<br>10위권 일관객 합계: %{y:,.0f}명<extra></extra>',
    )
    # 날짜가 서로 가까워도 읽기 쉽도록 주석을 상단 세 칸에 나눕니다.
    for i, (_, row) in enumerate(top_days.sort_values('날짜').iterrows()):
        fig.add_annotation(
            x=row['날짜'], y=row['일관객 합계'], xref='x', yref='y',
            text=row['날짜'].strftime('%Y-%m-%d'),
            ax=daily['날짜'].min() + (daily['날짜'].max() - daily['날짜'].min()) * ((i + 0.5) / 3), axref='x',
            ay=daily['일관객 합계'].max() * 1.15, ayref='y',
            showarrow=True, arrowhead=2, arrowcolor='#D94841',
            bgcolor='white', bordercolor='#D94841', borderpad=4,
            font={'color': '#A52A2A', 'size': 12},
        )
    fig.update_layout(height=500, margin={'t': 90}, hovermode='closest')
    fig.update_xaxes(tickformat='%Y-%m-%d')
    fig.update_yaxes(tickformat=',.0f', rangemode='tozero')
    st.plotly_chart(fig, width='stretch', key='graph_3_daily_total')
    show_insight(GRAPH_3_INSIGHT)
    st.caption('합계는 그날 박스오피스 10위권 영화의 기록만 더한 값으로, 전체 영화 관객수와는 다릅니다. 합계가 같으면 날짜가 이른 날부터 표시합니다.')

# ============================================================
# 5. 그래프 4 — 영화별 기간 내 일관객 합계 TOP 10
# ============================================================
def make_top_ten_summary(df):
    # 영화코드로 묶어 동명 영화를 구분하며, 날짜 수는 중복 없이 셉니다.
    summary = (
        df.loc[df['순위'].between(1, 10)]
        .groupby('영화코드', as_index=False)
        .agg(영화명=('영화명', 'first'),
             일관객합계=('일관객', 'sum'),
             진입일수=('날짜', 'nunique'))
        .sort_values(['일관객합계', '영화코드'], ascending=[False, True])
        .head(10).copy()
    )
    duplicates = summary['영화명'].duplicated(keep=False)
    summary['영화'] = summary['영화명']
    summary.loc[duplicates, '영화'] = (
        summary.loc[duplicates, '영화명'] + ' ('
        + summary.loc[duplicates, '영화코드'].astype(str) + ')'
    )
    return summary


def show_top_ten_bar(df):
    st.header('4. 영화별 일관객 합계 TOP 10')
    summary = make_top_ten_summary(df)
    if summary.empty:
        st.info('표시할 10위권 기록이 없습니다.')
        return
    fig = px.bar(
        summary, x='일관객합계', y='영화', orientation='h',
        custom_data=['진입일수'],
        labels={'일관객합계': '기간 내 일관객 합계 (명)', '영화': '영화'},
        color_discrete_sequence=['#4682B4'],
    )
    # 내림차순 목록의 첫 영화를 맨 위에 표시합니다.
    fig.update_yaxes(
        categoryorder='array', categoryarray=summary['영화'].tolist(),
        autorange='reversed', automargin=True,
    )
    fig.update_xaxes(tickformat=',.0f', rangemode='tozero')
    fig.update_traces(
        hovertemplate='영화: %{y}<br>기간 내 일관객 합계: %{x:,.0f}명<br>기간 내 10위권 진입일수: %{customdata[0]:,.0f}일<extra></extra>'
    )
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, width='stretch', key='graph_4_top_ten')
    show_insight(GRAPH_4_INSIGHT)
    st.caption('합계와 진입일수는 이 데이터 기간의 10위권 기록만을 기준으로 합니다. 개봉일과 기간 밖 기록이 없어 개봉 이후 전체 진입일수는 알 수 없습니다.')

# ============================================================
# 6. 그래프 5 — 월 × 요일 일관객 합계 히트맵
# ============================================================
def make_month_weekday_summary(df):
    records = df.loc[df['순위'].between(1, 10)].copy()
    # 서로 다른 연도의 같은 달을 합치지 않도록 연월을 사용합니다.
    records['월'] = records['날짜'].dt.strftime('%Y-%m')
    records['요일번호'] = records['날짜'].dt.dayofweek  # 월요일=0, 일요일=6
    matrix = records.groupby(['월', '요일번호'])['일관객'].sum().unstack('요일번호')
    matrix = matrix.sort_index().reindex(columns=range(7))
    matrix.columns = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    return matrix


def show_month_weekday_heatmap(df):
    st.header('5. 월 × 요일별 일관객 합계')
    matrix = make_month_weekday_summary(df)
    if matrix.empty:
        st.info('표시할 10위권 기록이 없습니다.')
        return
    fig = px.imshow(
        matrix, aspect='auto', origin='upper',
        color_continuous_scale='Blues', zmin=0,
        labels={'x': '요일', 'y': '월', 'color': '일관객 합계 (명)'},
    )
    fig.update_traces(
        hovertemplate='월: %{y}<br>요일: %{x}<br>일관객 합계: %{z:,.0f}명<extra></extra>',
        hoverongaps=False,
    )
    fig.update_xaxes(
        type='category', categoryorder='array', categoryarray=matrix.columns.tolist(),
        side='bottom',
    )
    fig.update_yaxes(
        type='category', categoryorder='array', categoryarray=matrix.index.tolist(),
        autorange='reversed',
    )
    fig.update_layout(
        height=max(420, len(matrix) * 35 + 120),
        coloraxis_colorbar={'tickformat': ',.0f'},
    )
    st.plotly_chart(fig, width='stretch', key='graph_5_month_weekday')
    show_insight(GRAPH_5_INSIGHT)
    st.caption('각 칸은 해당 월·요일의 10위권 일관객 합계이며, 색이 진할수록 관객이 많습니다. 합계는 기록된 날짜 수의 영향도 받으며, 기록이 없는 조합은 빈칸으로 표시합니다.')

# ============================================================
# 7. 다음 그래프 추가 공간
# 새 그래프는 함수로 작성하고 main()에서 호출하세요.
# 그래프 아래에는 show_insight('이 그래프의 해석 한 문장')를 넣으세요.
# ============================================================


def main():
    st.title(TITLE)
    st.write('영화를 골라 날짜에 따른 관객수 변화를 살펴보세요.')
    try:
        df = load_data(DATA_URL)
    except Exception as exc:
        st.error('데이터를 불러오지 못했습니다. 인터넷 연결과 데이터 주소를 확인한 뒤 새로고침해 주세요.')
        with st.expander('오류 내용 확인'):
            st.code(str(exc), language=None)
        st.stop()
    if df.empty:
        st.info('표시할 영화 데이터가 없습니다.')
        st.stop()
    st.caption(f'데이터 기간: {df["날짜"].min():%Y-%m-%d} ~ {df["날짜"].max():%Y-%m-%d} · {df["날짜"].nunique():,}일')
    st.divider()
    show_daily_audience(df)
    st.divider()
    show_top_five(df)
    st.divider()
    show_daily_total(df)
    st.divider()
    show_top_ten_bar(df)
    st.divider()
    show_month_weekday_heatmap(df)
    st.divider()
    st.header('6. 다음 그래프')
    st.caption('새로운 그래프를 추가할 공간입니다.')


if __name__ == '__main__':
    main()
