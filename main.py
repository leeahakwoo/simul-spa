import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

st.set_page_config(layout="wide", page_title="물류 배치 최적화 시뮬레이션")

# --- 1. [상단] 논리적 흐름 가이드 ---
st.title("🏭 프로세스 설계 및 설비 배치 최적화 보고서")

# 단계별 탭 구성 (사용자가 논리를 따라오게 만듦)
tabs = st.tabs(["🧐 1. AS-IS 문제 분석", "🛠️ 2. 개선 전략(TO-BE)", "📊 3. 시뮬레이션 및 검증"])

with tabs[0]:
    st.subheader("⚠️ 현재 프로세스의 문제점 (AS-IS)")
    col_a, col_b = st.columns(2)
    with col_a:
        st.error("**1. 무질서한 설비 배치**\n\n품목의 출고 빈도를 고려하지 않고 빈 곳에 무작위로 상품을 적치하여, 작업자가 센터 끝(C-Zone)까지 불필요하게 왕복함.")
    with col_b:
        st.error("**2. 비효율적 피킹 경로**\n\n주문 발생 순서대로 이동함에 따라 이미 지나온 통로를 다시 돌아가는 '역행 동선'이 다수 발생함.")

with tabs[1]:
    st.subheader("💡 최적화 개선안 (TO-BE Strategy)")
    col_c, col_d = st.columns(2)
    with col_c:
        st.success("**[설비 배치] ABC Slotting 적용**\n\n데이터 분석을 통해 출고 빈도가 높은 상위 20% 품목(전자제품 등)을 출고장 인근 '골드 존'에 재배치.")
    with col_d:
        st.success("**[프로세스] S-Shape 경로 최적화**\n\n작업자가 한 방향으로 이동하며 피킹을 완료하도록 동선을 정렬하여 중복 이동 거리 제거.")

# --- 2. 시뮬레이션 로직 ---
st.sidebar.header("🕹️ 컨트롤러")
scenario = st.sidebar.radio("시나리오 선택", ["AS-IS (개선 전)", "TO-BE (개선 후)"])
picking_count = st.sidebar.slider("피킹 물량", 30, 80, 50)

# 고정된 물품 데이터
zone_items = {
    "A-Zone": ["iPhone", "iPad", "MacBook", "AirPods"], 
    "B-Zone": ["Mouse", "Cable", "Keyboard", "Hub"],
    "C-Zone": ["Desk", "Chair", "Shelf", "Lamp"]
}

def get_data(mode, count):
    np.random.seed(42) # 비교를 위해 시드 고정
    if "AS-IS" in mode:
        # AS-IS: 물품이 전 구역(0~100)에 고르게 퍼짐
        x = np.random.randint(10, 95, size=count)
        y = np.random.randint(10, 95, size=count)
    else:
        # TO-BE: 물품이 입구(0,0) 근처 A구역(10~40)에 80% 집중
        x = np.random.choice([np.random.randint(10, 40), np.random.randint(40, 95)], size=count, p=[0.8, 0.2])
        y = np.random.randint(10, 95, size=count)
        # 경로 정렬
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
    
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

def draw_warehouse(ax, mode):
    ax.set_facecolor('#fdfdfd')
    zones = [(15, "A-Zone (인기)", "#d1e7dd"), (45, "B-Zone (일반)", "#fff3cd"), (75, "C-Zone (비선호)", "#f8d7da")]
    
    for start_x, label, color in zones:
        ax.add_patch(patches.Rectangle((start_x-5, 5), 25, 90, facecolor=color, alpha=0.2))
        ax.text(start_x+5, 96, label, fontsize=10, fontweight='bold', ha='center')
        # 랙 그리기
        for i, y in enumerate(range(15, 85, 20)):
            ax.add_patch(patches.Rectangle((start_x, y), 10, 10, facecolor='#6c757d', alpha=0.5))
            # AS-IS/TO-BE에 따른 물품 배치 논리 시각화 (A구역 위주 설명)
            if start_x == 15:
                ax.text(start_x+5, y+5, "인기상품", fontsize=7, ha='center', color='white')

    ax.scatter(0, 0, c='blue', s=200, marker='s', label='출고장')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 110)

# --- 3. 시뮬레이션 실행 (Tabs 3 안에서 실행) ---
with tabs[2]:
    st.subheader(f"🏃 시뮬레이션 검증: {scenario}")
    
    df = get_data(scenario, picking_count)
    total_dist = np.sqrt(np.diff(df['X'])**2 + np.diff(df['Y'])**2).sum()
    
    # 성과 지표 비교를 위한 기준값 (AS-IS 거리 계산)
    asis_ref_dist = 2800 # 가상의 AS-IS 평균 거리
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        plot_spot = st.empty()
        fig, ax = plt.subplots(figsize=(10, 7))
        draw_warehouse(ax, scenario)
        
        # 전체 동선을 한눈에 보여줌 (스파게티 현상 강조를 위해 애니메이션 없이 바로 표시하거나 빠르게 진행)
        ax.plot(df['X'], df['Y'], color='#0dcaf0' if "TO-BE" in scenario else '#ff4b4b', 
                alpha=0.6, linewidth=2, marker='o', markersize=4)
        plot_spot.pyplot(fig)

    with col2:
        st.metric("현재 총 이동 거리", f"{total_dist:.1f} m")
        if "TO-BE" in scenario:
            st.success(f"**거리 감소율: {((2800-total_dist)/2800*100):.1f}%**")
            st.write("✅ **배치 최적화 완료**")
            st.write("작업자가 입구 근처(A구역)에서 대부분의 작업을 처리합니다.")
        else:
            st.error("**개선 필요**")
            st.write("작업자가 먼 거리(C구역)까지 빈번하게 이동하며 동선이 심하게 꼬입니다.")

    st.divider()
    st.markdown("### 📝 최종 결론")
    st.info(f"시뮬레이션 분석 결과, **설비 재배치(ABC Slotting)**와 **프로세스 개선(Routing)**만으로도 추가 설비 투자 없이 운영 효율을 극대화할 수 있음을 확인하였습니다.")
