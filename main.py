import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="물류센터 동선 최적화 시뮬레이션")

# --- 1. [상단] 과제 개요 및 시나리오 설명 ---
st.title("🎓 대학원 과제: 가상 물류센터 동선 및 스파게티 다이어그램 분석")
st.markdown("""
### 📝 과제 개요
본 프로젝트는 **스파게티 다이어그램(Spaghetti Diagram)** 방법론을 활용하여 물류센터 내 작업자의 이동 효율성을 시각적으로 분석합니다. 
데이터가 제한적인 상황을 고려하여, 실제 물류 로그 패턴을 반영한 가상 시나리오 데이터를 생성하고 최적화 전후의 성과를 비교합니다.

---
### 🏃 시나리오 가이드
좌측 사이드바에서 시나리오를 선택하면 각 상황에 맞는 작업자의 움직임이 시뮬레이션됩니다.
1. **평상시 (Normal Day):** 물품이 전 구역에 고르게 분포되어 무작위로 피킹하는 상황 (비효율 발생).
2. **주문 폭주 (Peak Day):** 특정 인기 품목 구역에 작업자가 몰려 병목 현상이 발생하는 상황.
3. **최적화 모델 (Optimized):** ABC 분석을 통해 빈도수가 높은 물품을 입구 근처에 배치하고 동선을 재정렬한 이상적 모델.
---
""")

# --- 2. 사이드바 설정 ---
st.sidebar.header("🕹️ 시뮬레이션 컨트롤러")
scenario = st.sidebar.selectbox("분석 시나리오 선택", 
    ["평상시 (Normal Day)", "주문 폭주 (Peak Day)", "최적화 모델 (Optimized)"])

picking_count = st.sidebar.slider("피킹 작업 물량 (건수)", 20, 100, 50)
speed = st.sidebar.select_slider("시뮬레이션 속도", options=["느림", "보통", "빠름"], value="보통")
speed_map = {"느림": 0.1, "보통": 0.05, "빠름": 0.01}

# --- 3. 데이터 생성 로직 ---
def get_scenario_data(mode, count):
    np.random.seed(42)
    if mode == "평상시 (Normal Day)":
        x = np.random.randint(10, 90, size=count)
        y = np.random.randint(10, 90, size=count)
    elif mode == "주문 폭주 (Peak Day)":
        x = np.random.normal(40, 10, size=count).clip(5, 95)
        y = np.random.normal(40, 10, size=count).clip(5, 95)
    else: # Optimized
        x = np.random.exponential(scale=20, size=count).clip(5, 95)
        y = np.random.randint(10, 90, size=count)
        # 경로 최적화 (정렬)
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
    
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
    ax.text(5, 85, "A-Zone (Fast)", color='green', alpha=0.5, fontweight='bold')
    ax.text(80, 85, "C-Zone (Slow)", color='red', alpha=0.5, fontweight='bold')
    ax.scatter(0, 0, c='blue', s=200, marker='s', label='Dock (Start/End)')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)

# --- 4. 메인 분석 영역 ---
df = get_scenario_data(scenario, picking_count)
total_dist = np.sqrt(np.diff(df['X'])**2 + np.diff(df['Y'])**2).sum()

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📍 실시간 동선 시각화 (Spaghetti Diagram)")
    st.write("작업자의 이동 경로를 추적하여 동선 꼬임 현상을 확인합니다.")
    plot_spot = st.empty()
    
    # 애니메이션 시뮬레이션
    for i in range(2, len(df)+1):
        fig, ax = plt.subplots(figsize=(10, 8))
        draw_layout(ax)
        path_df = df.iloc[:i]
        ax.plot(path_df['X'], path_df['Y'], color='#4dabf7', alpha=0.7, linewidth=2, marker='o', markersize=3)
        ax.scatter(path_df['X'].iloc[-1], path_df['Y'].iloc[-1], color='red', s=100, zorder=5) # 현재위치
        ax.set_title(f"현재 시나리오: {scenario} (진행률: {int(i/len(df)*100)}%)")
        plot_spot.pyplot(fig)
        time.sleep(speed_map[speed])
        plt.close()

with col2:
    st.subheader("📊 분석 리포트")
    st.metric("총 이동 거리", f"{total_dist:.2f} m")
    
    st.markdown("#### 🔍 관전 포인트")
    if scenario == "평상시 (Normal Day)":
        st.warning("작업자가 센터 곳곳을 불필요하게 왕복하고 있습니다. 선이 복잡하게 얽히는 '스파게티 현상'이 두드러집니다.")
    elif scenario == "주문 폭주 (Peak Day)":
        st.error("중앙 구역에 동선이 집중되어 작업자 간 충돌 위험과 병목 현상이 발생할 가능성이 높습니다.")
    else:
        st.success("동선이 정형화되어 있으며, 이동 거리가 획기적으로 단축되었습니다. ABC 배치의 효율성을 보여줍니다.")

    st.write("---")
    st.markdown("#### 📈 기대 효과")
    st.write(f"1. **거리 단축:** 최적화 시 약 {((2500-total_dist)/2500*100):.1f}% 감소 예상")
    st.write("2. **작업 효율:** 불필요한 보행 시간 감소로 시간당 피킹량(UPH) 향상")
    st.write("3. **안전:** 동선 단순화를 통한 작업자 간 충돌 방지")

# --- 5. 데이터 테이블 ---
st.write("---")
st.subheader("📋 시뮬레이션 원본 데이터 (Raw Data)")
st.caption("가상으로 생성된 작업자 위치 로그 데이터입니다.")
st.dataframe(df, use_container_width=True)
