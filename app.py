"""
생활용품 속 인공향료(프탈레이트) 노출 계산기 
----------------------------------------
고교 탐구주제: 생활용품 속 인공향료가 청소년 건강에 미치는 영향 및 해결방안

실행법:
    pip install streamlit pandas plotly
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# st.set_page_config(page_title="HealthLab | 인공향료 노출 시뮬레이션", page_icon="🧴", layout="wide")
st.set_page_config(page_title="HealthLab | 인공향료 노출 시뮬레이션", page_icon="healthlab_logo.png", layout="wide")


# ------------------------------------------------------------------
# 데이터 로드
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    konehs = pd.read_csv(DATA_DIR / "konehs_phthalate_streamlit.csv")
    nhanes = pd.read_csv(DATA_DIR / "nhanes_phthalate_trend.csv")
    coef = pd.read_csv(DATA_DIR / "product_metabolite_coefficients.csv")
    return konehs, nhanes, coef


konehs, nhanes, coef = load_data()

METABOLITE_INFO = {
    "MEHHP": "DEHP(디에틸헥실프탈레이트) 대사체 - 플라스틱 가소제 유래",
    "MEOHP": "DEHP 대사체",
    "MECPP": "DEHP 대사체",
    "MnBP": "DBP(디부틸프탈레이트) 대사체 - 매니큐어·화장품 유래",
    "MBzP": "BBzP(부틸벤질프탈레이트) 대사체",
    "MCOP": "DiNP 대사체",
    "MCPP": "DiNP/DiOP 계열 대사체",
    "MCNP": "DiDP 대사체",
    "MEP": "DEP(디에틸프탈레이트) 대사체 - 향수·화장품 향료 유래 (5기부터 측정)",
    "MMP": "DMP(디메틸프탈레이트) 대사체 (5기부터 측정)",
}

AGE_LABEL = {
    "preschool": "영유아",
    "elementary": "초등학생",
    "middle_high_school": "중고등학생",
    "adult": "성인",
}


# ------------------------------------------------------------------
# 사이드바 네비게이션
# ------------------------------------------------------------------
# 로고 이미지 삽입 (사이드바 상단)
st.sidebar.image("healthlab_logo.png", use_container_width=True)

st.sidebar.title("MENU")
page = st.sidebar.radio(
    label =  "",
    options = ["📊 인공향료 노출 현황 (통계)", "🧮 나의 하루 노출지수 계산기"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "이 앱은 국립환경과학원 국민환경보건기초조사(KoNEHS) 원자료와 "
    "국내외 학술 문헌을 기반으로 제작된 교육용 시뮬레이션입니다. "
    "실제 개인 건강 진단 목적으로 사용할 수 없습니다."
)


# ==================================================================
# PAGE 1. 인구집단 노출 현황
# ==================================================================
if page == "📊 인공향료 노출 현황 (통계)":
    st.title("📊 우리나라 국민의 프탈레이트(인공향료 유래) 노출 현황")
    st.write("국립환경과학원이 실제로 측정한 요중(소변) 프탈레이트 대사체 농도 데이터입니다.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        metabolite_sel = st.selectbox(
            "대사체 선택", options=list(METABOLITE_INFO.keys()),
            format_func=lambda x: f"{x} ({METABOLITE_INFO[x]})",
            key="tab1_metabolite",
        )
    with col_b:
        years_with_all_ages = sorted(
            konehs[konehs["age_group_en"] == "middle_high_school"]["year"].unique(), reverse=True
        )
        year_sel = st.selectbox("조사연도", options=years_with_all_ages, key="tab1_year")

    d = konehs[
        (konehs["metabolite"] == metabolite_sel)
        & (konehs["year"] == year_sel)
        & (konehs["statistic"] == "geometric_mean")
    ].copy()
    d["age_label"] = d["age_group_en"].map(AGE_LABEL)
    order = ["영유아", "초등학생", "중고등학생", "성인"]
    d["age_label"] = pd.Categorical(d["age_label"], categories=order, ordered=True)
    d = d.sort_values("age_label")

    if d.empty:
        st.warning("해당 연령대 데이터가 없습니다.")
    else:
        fig = px.bar(
            d, x="age_label", y="value", color="age_label",
            labels={"age_label": "연령대", "value": "농도 (µg/L, 기하평균)"},
            title=f"{metabolite_sel} 연령대별 요중 농도 ({year_sel}년 조사)",
            text_auto=".2f",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        teen_val = d[d["age_label"] == "중고등학생"]["value"].values
        adult_val = d[d["age_label"] == "성인"]["value"].values
        if len(teen_val) and len(adult_val) and adult_val[0] > 0:
            ratio = teen_val[0] / adult_val[0]
            if ratio > 1:
                st.info(f"💡 중고등학생 농도가 성인의 **{ratio:.2f}배**로 더 높습니다.")
            else:
                st.info(f"💡 중고등학생 농도는 성인의 {ratio:.2f}배 수준입니다.")

    st.caption(
        "📌 출처: 기후에너지환경부 국립환경과학원, 국민환경보건기초조사 (1~3기 원자료 data.go.kr/data/3075219, "
        "5기(2021-2023) KOSIS 공식 통계표)"
    )


# ==================================================================
# PAGE 2. 개인별 노출지수 계산기
# ==================================================================
elif page == "🧮 나의 하루 노출지수 계산기":
    st.title("🧮 나의 하루 인공향료 노출지수 계산기")
    st.write(
        "오늘 하루 사용한 생활용품을 체크하고 사용 횟수를 입력하면, "
        "국내외 역학연구를 근거로 한 **상대적 노출지수**를 계산해줍니다."
    )

    with st.expander("⚠️ 반드시 읽어주세요 - 이 계산기가 측정하는 것과 측정하지 않는 것", expanded=True):
        st.markdown(
            """
- 이 지수는 실제 체내 농도(㎍/L)를 계산하는 것이 아닙니다. 정확한 개인별 흡수량 계산에는
  제품별 프탈레이트 함량 실측 데이터와 개인 생체시료 분석이 필요합니다.
- 대신, "이 제품을 사용한 사람들의 요중 대사체 농도가 통계적으로 얼마나 더 높게 관찰되었는가"를
  보여준 실제 역학연구(주로 미국 EARTH Study, Braun et al. 2014)의 수치를 근거로,
  여러 제품을 함께 사용했을 때의 상대적 노출 가능성을 합산해서 보여주는 교육용 지표입니다.
- 정량적 연구가 있는 항목(향수, 데오드란트, 헤어스프레이 등)은 % 증가율로,
  정량 연구는 없지만 연관성만 보고된 항목(로션, 색조화장품 등)은 "연관 있음"으로 따로 표시합니다.
- 아래 계산 결과에 마우스를 올리거나 펼침 메뉴를 클릭하면 각 수치의 정확한 출처를 확인할 수 있습니다.
            """
        )

    st.subheader("오늘 사용한 제품을 체크하세요")

    quant = coef[coef["evidence_type"] == "quantitative"].reset_index(drop=True)
    qual = coef[coef["evidence_type"] == "qualitative"].reset_index(drop=True)

    st.markdown("**① 정량적 연구가 있는 제품** (% 증가율 근거 있음)")
    quant_inputs = {}
    cols = st.columns(2)
    for i, row in quant.iterrows():
        with cols[i % 2]:
            used = st.checkbox(f"{row['product_kr']}", key=f"q_{i}")
            count = 0
            if used:
                count = st.number_input(
                    f"　오늘 {row['product_kr']} 사용 횟수", min_value=1, max_value=10, value=1, key=f"qc_{i}"
                )
            quant_inputs[row["product_kr"]] = (used, count, row)

    st.markdown("**② 연관성만 보고된 제품** (정량 계수 없음, 참고용)")
    qual_inputs = {}
    cols2 = st.columns(2)
    for i, row in qual.iterrows():
        with cols2[i % 2]:
            used = st.checkbox(f"{row['product_kr']}", key=f"ql_{i}")
            qual_inputs[row["product_kr"]] = (used, row)

    st.markdown("---")
    calc = st.button("🔍 노출지수 계산하기", type="primary", use_container_width=True)

    if calc:
        used_quant = [(k, v[1], v[2]) for k, v in quant_inputs.items() if v[0]]
        used_qual = [(k, v[1]) for k, v in qual_inputs.items() if v[0]]

        if not used_quant and not used_qual:
            st.warning("체크된 제품이 없습니다. 최소 1개 이상 선택해주세요.")
        else:
            st.subheader("📈 계산 결과")

            # 정량 지수 (MEP 기준 상대 증가율 - 단순 합산, 사용횟수는 참고 표시만)
            total_pct = sum(float(row["effect_value"]) for _, _, row in used_quant)
            col1, col2 = st.columns([1, 1])

            with col1:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=total_pct,
                    title={"text": "MEP 관련 상대 노출지수 (% 증가 추정)"},
                    gauge={
                        "axis": {"range": [0, 300]},
                        "bar": {"color": "darkorange"},
                        "steps": [
                            {"range": [0, 80], "color": "#d4f7d4"},
                            {"range": [80, 160], "color": "#fff3b0"},
                            {"range": [160, 300], "color": "#ffb3b3"},
                        ],
                    },
                ))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with col2:
                st.markdown("**선택한 제품별 기여도**")
                for name, cnt, row in used_quant:
                    st.write(f"- {name} (오늘 {cnt}회): **+{row['effect_value']}%** (MEP 기준)")

                mep_baseline = konehs[
                    (konehs["metabolite"] == "MEP")
                    & (konehs["age_group_en"] == "middle_high_school")
                    & (konehs["year"] == 2023)
                    & (konehs["statistic"] == "geometric_mean")
                ]
                if not mep_baseline.empty:
                    base_val = mep_baseline["value"].values[0]
                    estimated = base_val * (1 + total_pct / 100)
                    st.markdown(
                        f"국내 중고등학생 평균: **{base_val} µg/L** → "
                        f"오늘 추정치: **약 {estimated:.1f} µg/L**"
                    )
                    st.caption(
                        "⚠️ 이 추정치는 '평균적으로 이 정도 더 높게 관찰되었다'는 미국 역학연구 계수를 "
                        "한국 KoNEHS 기하평균에 단순 적용한 참고값이며, 실제 개인 체내 농도와 다를 수 있습니다."
                    )

                if used_quant:
                    with st.expander("출처 보기"):
                        for name, cnt, row in used_quant:
                            st.caption(f"{name}: {row['source']} — {row['source_url']}")
                        st.caption(
                            "MEP 기준값 출처: 국립환경과학원 국민환경보건기초조사 5기(2021-2023), KOSIS"
                        )

            if used_qual:
                st.markdown("**③ 연관성이 보고된 제품과 국내 KoNEHS 측정 대사체 비교**")
                st.write("아래 제품들은 정량적 증가율은 없지만, 사용 시 특정 대사체 농도가 더 높게 관찰된다고 보고되었습니다.")
                for name, row in used_qual:
                    baseline = konehs[
                        (konehs["metabolite"] == row["metabolite"])
                        & (konehs["age_group_en"] == "middle_high_school")
                        & (konehs["year"] == 2017)
                        & (konehs["statistic"] == "geometric_mean")
                    ]
                    base_val = baseline["value"].values[0] if not baseline.empty else None
                    with st.expander(f"{name} → {row['metabolite']} 연관"):
                        st.write(f"국내 중고등학생 {row['metabolite']} 기하평균(2017년 KoNEHS): "
                                 f"**{base_val if base_val is not None else '자료없음'} µg/L**")
                        st.caption(f"연관성 출처: {row['source']} — {row['source_url']}")

            st.info(
                "이 지수가 높다고 해서 특정 질병이 발생한다는 의미는 아닙니다. "
                "다만 프탈레이트류는 내분비계 교란물질로 분류되어 반복적/복합적 노출을 줄이는 것이 "
                "일반적으로 권장됩니다. (무향/무프탈레이트 표시 제품 사용, 사용량 줄이기 등)"
            )


# ==================================================================
# PAGE 3. 전체 출처
# ==================================================================
else:
    st.title("ℹ️ 이 앱이 사용한 모든 데이터의 출처")

    st.subheader("1. 국내 인체 바이오모니터링 데이터")
    st.markdown(
        """
        - **국민환경보건 기초조사(KoNEHS)** 1~3기 원자료 (2011·2014·2017년)
          제공: 기후에너지환경부 국립환경과학원 / 공공데이터포털
          링크: https://www.data.go.kr/data/3075219/fileData.do
        - **국민환경보건 기초조사 5기** (2021-2023년, 청소년 901명 포함)
          제공: KOSIS 국가통계포털
          비고: MEP·MMP 대사체가 5기부터 신규 측정됨
        - 4기(2018-2020)는 원자료가 아직 공개되지 않아 이 앱에는 포함되어 있지 않습니다.
        - 국가승인통계 제106027호
        """
    )

    st.subheader("2. 미국 인체 바이오모니터링 데이터")
    st.markdown(
        """
        - **CDC NHANES** 기반 US EPA 발표 수치
        - 링크: https://www.epa.gov/americaschildrenenvironment/biomonitoring-phthalates
        - 링크: https://cfpub.epa.gov/roe/technical-documentation.cfm?i=67
        """
    )

    st.subheader("3. 제품 사용 - 대사체 연관성 (개인 노출지수 계산 근거)")
    st.dataframe(coef, use_container_width=True)

    st.caption(
        "이 앱은 교육 목적의 탐구활동 산출물입니다. 실측되지 않은 값은 절대 임의로 채우지 않았으며, "
        "정량 데이터가 없는 항목은 명시적으로 '연관성만 보고됨'으로 표시했습니다."
    )
