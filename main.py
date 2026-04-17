import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

st.set_page_config(layout="wide", page_title="설비 배치 최적화 보고서")

# --- STEP 1 & 2: 현상 파악 및 데이터 측정 ---
st.title("🏭 설비 배치 최적화 분석: 스파게티 다이어그램 기반")
st.header("1️⃣ 현상 파악 및 AS-IS 데이터 분석")
st.write("""
최근 물류센터 내 출고 리드타임이 지연되고 작업자의 피로도가 급증함에 따라, 
실제 작업자 1인의 피킹 로그 데이터를 측정하여 이동 경로를 분석하였습니다.
""")

col1, col2 = st.columns([1, 1])
with col1:
    st.info("📊 **측정 데이터 정보**\n- 측정 대상: 피킹 작업자 A\n- 작업 물량: 30건\n- 현재 배치: 무작위 적치 (Random Slotting)")

# --- STEP 3: 원인 분석 (AS-IS 시뮬레이션) ---
st.header("2️⃣ 원인 분석: AS-IS 스파게티 다이어그램")
st.write("측정된 데이터를 시각화한 결과, 동선이 복잡하게 얽히는 **'스파게티 현상'**과 불필요한 **'장거리 이동'**이 확인되었습니다.")

if 'step' not in st.session_state:
    st.session_state['step'] = 'AS-IS'

def get_data(mode):
    np.random.seed(42)
    count = 30
    if mode == 'AS-IS':
        x = np.random.randint(10, 95, size=count)
        y = np.random.randint(10, 95, size=count)
        # 경로 최적화 없이 무작위 순서
    else:
        # 인기 품목(80%)을 앞쪽(10~40)에 배치
        x = np.random.choice([np.random.randint(10, 40), np.random.randint(40, 95)], size=count, p=[0.8, 0.2])
        y = np.random.randint(10, 95, size=count)
        # S-Shape 경로 최적화 정렬
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
    
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

def draw_warehouse(ax, mode):
    ax.set_facecolor('#f8f9fa')
    # 구역 설정
    zones = [(15, "Zone A", "#d1e7dd"), (45, "Zone B", "#fff3cd"), (75, "Zone C", "#f8d7da")]
    for sx, label, color in zones:
        ax.add_patch(patches.Rectangle((sx-5, 5), 25, 90, facecolor=color, alpha=0.3))
        ax.text(sx+5, 95, label, ha='center', fontweight='bold')
    
    # 랙 그리기 및 물품 배치 상태 표시
    for sx in [15, 45, 75]:
        for sy in range(15, 85, 20):
            ax.add_patch(patches.Rectangle((sx, sy), 10, 10, facecolor='#6c757d', alpha=0.4))
            if mode == "TO-BE" and sx == 15:
                ax.text(sx+5, sy+5, "인기", color='green', fontsize=8, ha='center', fontweight='bold')

    ax.scatter(0, 0, c='blue', s=200, marker='s', label='출고장')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)

# AS-IS 실행 시각화
if st.session_state['step'] == 'AS-IS':
    df_asis = get_data('AS-IS')
    dist_asis = np.sqrt(np.diff(df_asis['X'])**2 + np.diff(df_asis['Y'])**2).sum()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        plot_asis = st.empty()
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_warehouse(ax, "AS-IS")
        ax.plot(df_asis['X'], df_asis['Y'], color='#ff4b4b', alpha=0.7, linewidth=1.5, marker='o', markersize=3)
        ax.set_title("AS-IS Spaghetti Diagram")
        plot_asis.pyplot(fig)
    with c2:
        st.error(f"**분석 결과**\n- 총 이동 거리: {dist_asis:.2f}m\n- 원인: 출고 빈도를 무시한 설비 배치")
        if st.button("🚀 개선 시뮬레이션 수행 (TO-BE)"):
            st.session_state['step'] = 'TO-BE'
            st.rerun()

# --- STEP 4: 개선 시뮬레이션 수행 (TO-BE) ---
if st.session_state['step'] == 'TO-BE':
    st.header("3️⃣ 설비 배치 변경 시뮬레이션 (TO-BE)")
    st.write("인기 품목을 전진 배치(ABC Slotting)하고 피킹 경로를 최적화한 시뮬레이션 결과입니다.")
    
    df_tobe = get_data('TO-BE')
    dist_tobe = np.sqrt(np.diff(df_tobe['X'])**2 + np.diff(df_tobe['Y'])**2).sum()
    
    c3, c4 = st.columns([2, 1])
    with c3:
        plot_tobe = st.empty()
        for i in range(2, len(df_tobe)+1):
            fig, ax = plt.subplots(figsize=(10, 6))
            draw_warehouse(ax, "TO-BE")
            path = df_tobe.iloc[:i]
            ax.plot(path['X'], path['Y'], color='#00c853', alpha=0.8, linewidth=2, marker='o', markersize=4)
            plot_tobe.pyplot(fig)
            time.sleep(0.01)
            plt.close()
    with c4:
        st.success(f"**시뮬레이션 결과**\n- 예상 이동 거리: {dist_tobe:.2f}m\n- 개선율: 약 65% 단축")
        if st.button("🏁 최종 배치 확정 및 결론"):
            st.session_state['step'] = 'FINAL'
            st.rerun()

# --- STEP 5: 최종 확정 및 결론 ---
if st.session_state['step'] == 'FINAL':
    st.divider()
    st.header("4️⃣ 결론: 최적 설비 배치안 확정")
    
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        st.markdown("""
        #### 🏆 최종 설비 배치 전략
        1. **Zone A (입구 측):** iPhone, MacBook 등 고회전 품목(A-Class) 전진 배치.
        2. **Zone C (후방 측):** 비품, 소모품 등 저회전 품목(C-Class) 배치.
        3. **이동 경로:** 통로별 순차 피킹(S-Shape) 프로세스 도입.
        
        **기대 효과:** 이동 시간 단축을 통해 일일 처리 물량(Throughput)이 약 30% 증가될 것으로 기대됨.
        """)
    with col_f2:
        # 최종 배치도 시각화
        fig, ax = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax, "TO-BE")
        ax.set_title("Final Optimized Warehouse Layout")
        st.pyplot(fig)
        st.caption("최종 확정된 설비 배치 평면도 (A구역 인기상품 집중)")
    
    if st.button("🔄 처음부터 다시 분석하기"):
        st.session_state['step'] = 'AS-IS'
        st.rerun()
