import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="물류센터 동선 최적화 시뮬레이션")

# --- 1. [상단] 과제 개요 및 시나리오 설명 ---
st.title("🎓 대학원 과제: 가상 물류센터 동선 최적화 분석")
st.markdown("""
본 시뮬레이션은 데이터가 부재한 상황에서 **가상 피킹 로그**를 생성하여, 물류 센터의 고질적인 문제인 **동선 낭비**를 시각화하고 그 개선 방안을 제시합니다. 
스파게티 다이어그램을 통해 비효율을 확인하고, 최적화 알고리즘 적용 시의 성과를 비교할 수 있습니다.
""")

# --- 개선 방법론 설명 섹션 ---
with st.expander("🔍 본 시뮬레이션에 적용된 개선 방법론 (Methodology)"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        **1. ABC 배치 최적화 (Slotting Strategy)**
        - **AS-IS:** 물품의 출고 빈도와 상관없이 임의의 랙(Rack)에 배치됨.
        - **TO-BE:** 출고 빈도가 높은 상위 20% 품목(A-Class)을 출고장 근처에 집중 배치하여 평균 이동 거리 단축.
        """)
    with col_b:
        st.markdown("""
        **2. 피킹 경로 최적화 (Routing Optimization)**
        - **AS-IS:** 주문 발생 순서(무작위)대로 이동하여 동선이 꼬이고 중복 이동 발생.
        - **TO-BE:** 위치 기반 정렬(S-Shape 로직)을 통해 작업자가 순차적으로 훑고 지나가도록 경로 최적화.
        """)

st.divider()

# --- 2. 사이드바 설정 ---
st.sidebar.header("🕹️ 시뮬레이션 컨트롤러")
scenario = st.sidebar.selectbox("분석 시나리오 선택", 
    ["개선 전: 평상시 (AS-IS)", "개선 전: 주문 폭주 (AS-IS)", "개선 후: 최적화 모델 (TO-BE)"])

picking_count = st.sidebar.slider("피킹 작업 물량 (건수)", 20, 100, 50)
speed = st.sidebar.select_slider("시뮬레이션 속도", options=["느림", "보통", "빠름"], value="보통")
speed_map = {"느림": 0.1, "보통": 0.05, "빠름": 0.01}

# --- 3. 데이터 생성 로직 ---
def get_scenario_data(mode, count):
    np.random.seed(42)
    if "평상시" in mode:
        x = np.random.randint(10, 90, size=count)
        y = np.random.randint(10, 90, size=count)
    elif "주문 폭주" in mode:
        x = np.random.normal(50, 20, size=count).clip(5, 95)
        y = np.random.normal(50, 20, size=count).clip(5, 95)
    else: # 개선 후 (TO-BE)
        # ABC 배치를 모사: 입구 근처에 많이 분포
        x = np.random.exponential(scale=20, size=count).clip(5, 95)
        y = np.random.randint(10, 90, size=count)
        # 경로 최적화: X축 기준 정렬
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
    
    # 시작/종료점 추가
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

def draw_layout(ax):
    ax.set_facecolor('#f8f9fa')
    # 랙 구역 그리기
    for x in range(15, 95, 20):
        for y in range(10, 90, 20):
            ax.add_patch(patches.Rectangle((x, y), 10, 15, facecolor='#dee2e6', edgecolor='#adb5bd', alpha=0.8))
    # 구역 라벨링
    ax.text(5, 90, "A-Zone (Fast Moving)", color='green', alpha=0.6, fontweight='bold')
    ax.text(80, 90, "C-Zone (Slow)", color='red', alpha=0.6, fontweight='bold')
    ax.scatter(0, 0, c='blue', s=200, marker='s', label='Dock (Start/End)', zorder=5)
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)

# --- 4. 메인 분석 및 시각화 영역 ---
df = get_scenario_data(scenario, picking_count)
total_dist = np.sqrt(np.diff(df['X'])**2 + np.diff(df['Y'])**2).sum()

# 컬럼 정의 (이 부분이 에러의 원인이었습니다!)
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📍 실시간 동선 시각화")
    plot_spot = st.empty()
    
    # 시뮬레이션 애니메이션
    for i in range(2, len(df)+1):
        fig, ax = plt.subplots(figsize=(10, 8))
        draw_layout(ax)
        path_df = df.iloc[:i]
        ax.plot(path_df['X'], path_df['Y'], color='#4dabf7', alpha=0.6, linewidth=2, marker='o', markersize=3)
        ax.scatter(path_df['X'].iloc[-1], path_df['Y'].iloc[-1], color='red', s=100, zorder=6) # 현재 위치
        ax.set_title(f"시나리오 실행 중: {scenario} (진행률: {int(i/len(df)*100)}%)")
        plot_spot.pyplot(fig)
        time.sleep(speed_map[speed])
        plt.close()

with col2:
    st.subheader("📊 분석 결과 리포트")
    st.metric("총 이동 거리", f"{total_dist:.2f} m")
    
    # 시나리오별 인사이트 제공
    st.markdown("#### 💡 분석 관전 포인트")
    if "평상시" in scenario:
        st.warning("작업자가 전 구역을 무질서하게 횡단하며 '스파게티 현상'이 나타납니다. 불필요한 공주행(Empty Travel)이 매우 많습니다.")
    elif "주문 폭주" in scenario:
        st.error("중앙 통로에 동선이 집중됩니다. 실제 현장에서는 작업자 및 장비 간 충돌 위험이 매우 높은 상태입니다.")
    else: # TO-BE
        improvement = ((2200 - total_dist) / 2200) * 100 # 가상의 기준점 대비
        st.success(f"**개선 완료!** 동선이 정형화되었으며, 거리 기준 약 {improvement:.1f}%의 효율 향상이 예상됩니다.")
        st.info("핵심: A-Zone에 물량을 집중시키고, 순차적 피킹 경로를 적용함.")

    st.divider()
    st.markdown("""
    #### 📈 종합 기대 효과
    1. **운영 비용 절감:** 보행 거리 감소로 인한 인건비 및 에너지 소모 절감.
    2. **작업 리드타임 단축:** 총 피킹 시간 감소로 빠른 출고 대응 가능.
    3. **안전성 확보:** 교차 동선 최소화를 통한 현장 사고 예방.
    """)

# --- 5. 데이터 하단 노출 ---
st.write("---")
st.subheader("📋 시뮬레이션 로그 데이터")
st.dataframe(df, use_container_width=True)
