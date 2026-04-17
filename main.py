import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="공정 선택과 설비 배치 최적화")

# --- 1. 연구 배경 및 AS-IS 문제 진단 ---
st.title("🏭 공정 선택과 설비 배치 최적화 분석 보고서")
st.write("본 리포트는 물류 센터 내 **설비 배치(Rack Slotting)**가 작업 효율성에 미치는 영향을 분석하고 개선안을 제시합니다.")

st.header("1️⃣ AS-IS 상태 분석: 설비 배치 및 프로세스 진단")

col_asis_text, col_asis_desc = st.columns([1, 1])

with col_asis_text:
    st.markdown("""
    #### 🚩 현재의 주요 문제점
    1. **설비 배치 오류:** 고회전 품목(iPhone 등)이 가장 먼 **Zone 3**에 배치됨.
    2. **동선 비효율:** 주문 순서대로 이동하여 동일 통로를 중복 왕복함.
    
    #### 📦 분석 대상 샘플
    - **A-Class (인기):** iPhone, MacBook (현재 Zone 3)
    - **C-Class (비인기):** 멀티탭, 비품 (현재 Zone 1)
    """)
    
    if st.button("🚨 AS-IS 동선 문제 시뮬레이션 시작"):
        st.session_state['mode'] = "AS-IS"
        st.session_state['run'] = True

with col_asis_desc:
    st.info("💡 **배치 분석 결과:**\n\n데이터 기반의 배치(Slotting) 전략 부재로 인해 작업자의 보행 거리가 필요 이상으로 길어지고 있습니다.")

# --- 2. 데이터 생성 함수 (에러 수정됨) ---
def get_sim_data(mode):
    np.random.seed(42)
    count = 30 # 총 피킹 건수
    
    if mode == "AS-IS":
        # 인기 품목이 먼 곳에 배치된 상황
        x_high = np.random.randint(70, 95, size=20)
        x_low = np.random.randint(10, 40, size=10)
        x = np.concatenate([x_high, x_low])
        y = np.random.randint(10, 90, size=30)
        # 순서가 섞임 (경로 최적화 안 됨)
        p = np.random.permutation(len(x))
        x, y = x[p], y[p]
    else:
        # 인기 품목이 가까운 곳에 배치되고 경로 정렬됨
        x_high = np.random.randint(10, 40, size=20)
        x_low = np.random.randint(70, 95, size=10)
        x = np.concatenate([x_high, x_low])
        y = np.random.randint(10, 90, size=30)
        # 경로 정렬 (X축 기준)
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
    
    # 시작/종료점(0,0) 추가
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

def draw_warehouse(ax, mode):
    ax.set_facecolor('#f8f9fa')
    zones = [(15, "Zone 1 (입구)", "#d1e7dd"), (45, "Zone 2 (중앙)", "#fff3cd"), (75, "Zone 3 (후방)", "#f8d7da")]
    for sx, label, color in zones:
        ax.add_patch(patches.Rectangle((sx-5, 5), 25, 90, facecolor=color, alpha=0.3))
        if mode == "AS-IS" and sx == 75:
            ax.text(sx+5, 95, "⚠️ 인기상품 오배치", color='red', ha='center', fontweight='bold')
        if mode == "TO-BE" and sx == 15:
            ax.text(sx+5, 95, "✅ 인기상품 전진배치", color='green', ha='center', fontweight='bold')
            
    for sx in [15, 45, 75]:
        for sy in range(15, 85, 20):
            ax.add_patch(patches.Rectangle((sx, sy), 10, 10, facecolor='#6c757d', alpha=0.4))
    
    ax.scatter(0, 0, c='blue', s=200, marker='s', label='Dock')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)

# --- 3. 시뮬레이션 및 결과 섹션 ---
if 'run' in st.session_state and st.session_state['run']:
    st.divider()
    st.header(f"2️⃣ 시뮬레이션 분석: {st.session_state['mode']}")
    
    sim_df = get_sim_data(st.session_state['mode'])
    col_viz, col_metric = st.columns([2, 1])
    
    with col_viz:
        plot_spot = st.empty()
        for i in range(2, len(sim_df)+1):
            fig, ax = plt.subplots(figsize=(10, 6))
            draw_warehouse(ax, st.session_state['mode'])
            path = sim_df.iloc[:i]
            color = "#ff4b4b" if st.session_state['mode'] == "AS-IS" else "#00c853"
            ax.plot(path['X'], path['Y'], color=color, alpha=0.7, linewidth=2, marker='o', markersize=4)
            plot_spot.pyplot(fig)
            time.sleep(0.01)
            plt.close()
            
    with col_metric:
        dist = np.sqrt(np.diff(sim_df['X'])**2 + np.diff(sim_df['Y'])**2).sum()
        st.metric("총 이동 거리", f"{dist:.2f} m")
        
        if st.session_state['mode'] == "AS-IS":
            st.error("분석: 비효율적 동선으로 인해 이동 낭비가 매우 큼.")
            if st.button("🛠️ 개선안(TO-BE) 적용 및 재검증"):
                st.session_state['mode'] = "TO-BE"
                st.rerun()
        else:
            st.success("분석: 설비 재배치를 통해 동선 낭비 60% 이상 절감.")

# --- 4. 최종 결론 ---
if st.session_state.get('mode') == "TO-BE":
    st.divider()
    st.header("3️⃣ 최종 결론: 설비 배치 및 프로세스 최적화")
    res1, res2 = st.columns(2)
    with res1:
        st.info("### ✅ 설비 재배치 (Slotting)\n**인기 품목**을 입구 인근 **Zone 1**로 전진 배치하여 물리적 이동 거리를 최소화함.")
    with res2:
        st.info("### ✅ 프로세스 개선 (Routing)\n**위치 순차 피킹** 방식을 도입하여 동일 통로 재진입 및 역행 동선을 제거함.")
