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
# 3. 다음 그래프 추가 공간
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
    st.header('2. 다음 그래프')
    st.caption('새로운 그래프를 추가할 공간입니다.')


if __name__ == '__main__':
    main()
