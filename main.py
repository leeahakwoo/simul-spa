import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 페이지 설정
st.set_page_config(layout="wide", page_title="물류센터 동선 최적화 시뮬레이션")

# --- 1. 가상 데이터 생성 함수 ---
def generate_warehouse_data(strategy="random", num_picks=40):
    np.random.seed(42)
    
    if strategy == "random":
        # AS-IS: 센터 전역에 무작위 분포 및 무작위 순서
        x = np.random.randint(10, 90, size=num_picks)
        y = np.random.randint(10, 90, size=num_picks)
    else:
        # TO-BE: ABC 분석 기반 배치 (A구역 위주) 및 경로 정렬
        # A구역(0~30), B구역(30~60), C구역(60~90) 가정
        x = np.random.choice([np.random.randint(10, 40), np.random.randint(40, 70), np.random.randint(70, 90)], 
                             size=num_picks, p=[0.7, 0.2, 0.1])
        y = np.random.randint(10, 90, size=num_picks)
        
        # 경로 최적화 (X축 순서대로 정렬하여 지그재그 이동 시뮬레이션)
        df_temp = pd.DataFrame({'x': x, 'y': y})
        df_temp = df_temp.sort_values(by=['x', 'y']).reset_index(drop=True)
        x, y = df_temp['x'].values, df_temp['y'].values

    # 시작/종료점(0,0) 추가
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    
    return pd.DataFrame({'X': x, 'Y': y})

# --- 2. 배경 레이아웃 그리기 함수 ---
def draw_warehouse_layout(ax):
    # 센터 외곽선
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    
    # 랙(Rack) 배치 시각화 (회색 박스들)
    for x in range(15, 95, 20): # 통로 간격
        for y in range(10, 90, 15):
            rect = patches.Rectangle((x, y), 10, 10, linewidth=1, edgecolor='gray', facecolor='#d3d3d3', alpha=0.5)
            ax.add_patch(rect)
    
    # 구역 표시
    ax.axvspan(10, 35, color='green', alpha=0.05, label='Zone A (High Freq)')
    ax.axvspan(35, 65, color='orange', alpha=0.05, label='Zone B (Medium)')
    ax.axvspan(65, 95, color='red', alpha=0.05, label='Zone C (Low)')
    
    # 입출고장 표시
    ax.scatter(0, 0, c='blue', s=200, marker='s', label='Entry/Exit', zorder=5)
    ax.text(-2, -8, "START/END", fontsize=10, fontweight='bold')

# --- 3. 메인 화면 구성 ---
st.title("🏭 가상 물류센터 스파게티 다이어그램 분석")
st.markdown("""
이 시뮬레이션은 작업자의 동선 데이터를 시각화하여 **이동 거리 낭비**를 분석합니다.  
**AS-IS**는 무작위 피킹 동선을, **TO-BE**는 구역별 최적화된 피킹 동선을 보여줍니다.
""")

# 데이터 생성
df_asis = generate_warehouse_data(strategy="random")
df_tobe = generate_warehouse_data(strategy="optimized")

# 거리 계산
dist_asis = np.sqrt(np.diff(df_asis['X'])**2 + np.diff(df_asis['Y'])**2).sum()
dist_tobe = np.sqrt(np.diff(df_tobe['X'])**2 + np.diff(df_tobe['Y'])**2).sum()

# 성과 지표
m1, m2, m3 = st.columns(3)
m1.metric("AS-IS 총 이동거리", f"{dist_asis:.1f} m")
m2.metric("TO-BE 총 이동거리", f"{dist_tobe:.1f} m", delta=f"-{((dist_asis-dist_tobe)/dist_asis*100):.1f}%")
m3.info("최적화 전략: ABC 배치 + 경로 정렬")

# 시각화
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚠️ AS-IS (개선 전 동선)")
    fig_asis, ax_asis = plt.subplots(figsize=(8, 8))
    draw_warehouse_layout(ax_asis) # 배경 그리기
    
    # 동선 그리기
    ax_asis.plot(df_asis['X'], df_asis['Y'], color='#e74c3c', alpha=0.7, linewidth=1.5, label='Picking Path')
    ax_asis.scatter(df_asis['X'], df_asis['Y'], c='black', s=15, zorder=4)
    ax_asis.legend(loc='upper right')
    st.pyplot(fig_asis)
    st.caption("현상: 작업자가 센터 전체를 무작위로 왕복하며 동선이 꼬임(Spaghetti).")

with col2:
    st.subheader("✅ TO-BE (개선 후 동선)")
    fig_tobe, ax_tobe = plt.subplots(figsize=(8, 8))
    draw_warehouse_layout(ax_tobe) # 배경 그리기
    
    # 동선 그리기
    ax_tobe.plot(df_tobe['X'], df_tobe['Y'], color='#2ecc71', alpha=0.8, linewidth=2, label='Optimized Path')
    ax_tobe.scatter(df_tobe['X'], df_tobe['Y'], c='black', s=15, zorder=4)
    ax_tobe.legend(loc='upper right')
    st.pyplot(fig_tobe)
    st.caption("개선: 빈도수가 높은 물품을 입구 근처(Zone A)에 배치하고 경로를 최단화함.")

# 데이터 테이블 표시
with st.expander("데이터 상세보기"):
    st.write("생성된 가상 피킹 로그 (상위 10개)")
    st.dataframe(df_asis.head(10))
