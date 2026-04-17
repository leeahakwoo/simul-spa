import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

st.set_page_config(layout="wide", page_title="물류센터 동선 시뮬레이터")

# --- 1. 시나리오 설정 ---
st.sidebar.title("🛠️ 시뮬레이션 설정")
scenario = st.sidebar.selectbox("시나리오 선택", 
    ["평상시 (Normal Day)", "블랙프라이데이 (주문폭주)", "긴급 재고조사"])

picking_count = st.sidebar.slider("피킹 물동량 (개수)", 10, 100, 40)
show_animation = st.sidebar.checkbox("이동 애니메이션 보기", value=True)

# --- 2. 데이터 생성 로직 (시나리오 반영) ---
def get_scenario_data(mode, count):
    np.random.seed(42)
    if mode == "평상시 (Normal Day)":
        x = np.random.randint(10, 90, size=count)
        y = np.random.randint(10, 90, size=count)
    elif mode == "블랙프라이데이 (주문폭주)":
        # 특정 구역(신선식품이나 인기상품)에 주문이 몰리는 상황 가정
        x = np.random.normal(50, 15, size=count).clip(10, 90)
        y = np.random.normal(50, 15, size=count).clip(10, 90)
    else: # 재고조사 (전 구역 순회)
        x = np.linspace(10, 90, count)
        y = np.sin(x/10)*40 + 50
    
    # 시작/종료점 추가
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

# --- 3. 배경 레이아웃 (공장 느낌 극대화) ---
def draw_detailed_layout(ax):
    ax.set_facecolor('#2c3e50') # 다크모드 공장 바닥 느낌
    # 랙(Rack) 그리기
    for x in range(15, 95, 15):
        for y in range(10, 90, 20):
            rect = patches.Rectangle((x, y), 8, 15, linewidth=1, edgecolor='#ecf0f1', facecolor='#95a5a6', alpha=0.3)
            ax.add_patch(rect)
    # 입출고 도크(Dock)
    ax.add_patch(patches.Rectangle((-5, 40), 5, 20, facecolor='#f1c40f'))
    ax.text(-12, 45, "DOCK 01", color='white', fontweight='bold', rotation=90)
    ax.set_xlim(-15, 105); ax.set_ylim(-5, 105)

# --- 4. 메인 화면 ---
st.title(f"🚀 시나리오 분석: {scenario}")
st.info(f"💡 현재 상황: {scenario}에 따른 작업자 동선 최적화 시뮬레이션을 수행합니다.")

df = get_scenario_data(scenario, picking_count)

col1, col2 = st.columns([2, 1])

with col1:
    placeholder = st.empty()
    
    # 애니메이션 구현
    if show_animation:
        for i in range(2, len(df)+1):
            fig, ax = plt.subplots(figsize=(10, 7))
            draw_detailed_layout(ax)
            sub_df = df.iloc[:i]
            # 지나온 길
            ax.plot(sub_df['X'], sub_df['Y'], color='#3498db', alpha=0.6, linewidth=2, marker='o', markersize=4)
            # 현재 위치 (작업자 아이콘 대신 큰 점)
            ax.scatter(sub_df['X'].iloc[-1], sub_df['Y'].iloc[-1], color='yellow', s=100, edgecolors='white', zorder=5)
            ax.set_title(f"작업 진행률: {int((i/len(df))*100)}%", color='white')
            placeholder.pyplot(fig)
            time.sleep(0.05)
            plt.close()
    else:
        fig, ax = plt.subplots(figsize=(10, 7))
        draw_detailed_layout(ax)
        ax.plot(df['X'], df['Y'], color='#3498db', alpha=0.8, linewidth=2, marker='o', markersize=4)
        placeholder.pyplot(fig)

with col2:
    st.subheader("📊 리포트 요약")
    total_dist = np.sqrt(np.diff(df['X'])**2 + np.diff(df['Y'])**2).sum()
    st.metric("총 이동 거리", f"{total_dist:.2f} m")
    
    # 몰입도를 위한 상황 멘트
    if total_dist > 1500:
        st.error("🚨 경고: 동선이 너무 길어 작업자 피로도가 높습니다!")
    else:
        st.success("✅ 양호: 동선 효율성이 적절한 수준입니다.")

    st.write("---")
    st.subheader("🧐 분석 결과")
    st.write(f"- {scenario} 상황에서는 중앙 통로 정체가 예상됩니다.")
    st.write("- 랙 사이의 회전 구간에서 속도 저하가 발생할 수 있습니다.")
    
    # 히트맵 분석 (간이 시각화)
    st.write("🔥 **병목 구간 예측**")
    st.caption("동선이 가장 많이 겹치는 지점(X,Y):")
    st.code(f"X: {df['X'].mode()[0]}, Y: {df['Y'].mode()[0]}")
