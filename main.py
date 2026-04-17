import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

st.set_page_config(layout="wide", page_title="설비 배치 최적화 리포트")

# --- 0. 초기 세션 상태 설정 ---
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 0
if 'sim_done' not in st.session_state:
    st.session_state['sim_done'] = False

# --- 1. 유틸리티 함수 ---
def get_data(mode, count, a_ratio=0.8):
    np.random.seed(42)
    a_count = int(count * a_ratio)
    c_count = count - a_count
    
    if mode == 'AS-IS':
        # AS-IS: 인기 품목이 먼 곳(Zone C)에 배치 + 경로 최적화 없음(무작위 순서)
        x_high = np.random.randint(70, 95, size=a_count)
        x_low = np.random.randint(10, 40, size=c_count)
        x = np.concatenate([x_high, x_low])
        y = np.random.randint(10, 90, size=count)
        p = np.random.permutation(len(x)) # 순서 섞기
        x, y = x[p], y[p]
    else:
        # TO-BE: 인기 품목 전진 배치(Zone A) + S-Shape Routing 적용
        x_high = np.random.randint(10, 40, size=a_count)
        x_low = np.random.randint(70, 95, size=c_count)
        x = np.concatenate([x_high, x_low])
        y = np.random.randint(10, 90, size=count)
        # S-Shape 정렬: 통로(X) 순서대로 가되, 지그재그나 순차적 이동 모사
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
        
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

def draw_warehouse(ax, mode):
    ax.set_facecolor('#f8f9fa')
    zones = [(15, "Zone A (입구/인기)", "#d1e7dd"), (45, "Zone B (중앙)", "#fff3cd"), (75, "Zone C (후방/비인기)", "#f8d7da")]
    for sx, label, color in zones:
        ax.add_patch(patches.Rectangle((sx-5, 5), 25, 90, facecolor=color, alpha=0.3))
        ax.text(sx+5, 95, label, ha='center', fontweight='bold', fontsize=10)
    
    for sx in [15, 45, 75]:
        for sy in range(15, 85, 20):
            ax.add_patch(patches.Rectangle((sx, sy), 10, 10, facecolor='#6c757d', alpha=0.4))
    ax.scatter(0, 0, c='blue', s=150, marker='s')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)

# --- 2. 상단 네비게이션 바 ---
st.title("📦 공정 설계 및 설비 배치 최적화")

nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
with nav_col1:
    if st.session_state['current_step'] > 0:
        if st.button("⬅️ 이전 단계"):
            st.session_state['current_step'] -= 1
            st.rerun()
with nav_col3:
    # 마지막 단계가 아니고, Step 3에서는 시뮬레이션이 끝난 경우에만 다음 버튼 활성화
    can_go_next = st.session_state['current_step'] < 3
    if st.session_state['current_step'] == 2 and not st.session_state.get('sim_done'):
        can_go_next = False
        
    if can_go_next:
        if st.button("다음 단계 ➡️"):
            st.session_state['current_step'] += 1
            st.rerun()

st.markdown("---")

# --- 3. 단계별 콘텐츠 ---

# [STEP 1. 배경 및 진단]
if st.session_state['current_step'] == 0:
    st.header("1️⃣ 배경 및 현상 분석")
    st.info("💡 **가이드:** 현재 물류 현장의 문제점을 데이터 관점에서 진단합니다.")
    st.markdown("""
    #### 🧐 핵심 당면 과제
    - **비효율의 원인:** 고회전 품목이 후방(Zone C)에 적치되어 피킹 보행 거리가 불필요하게 늘어남.
    - **프로세스 부재:** 데이터 기반의 피킹 경로(Routing) 알고리즘이 없어 현장에서 지연 발생.
    - **목표:** **ABC Slotting**과 **Routing Algorithm** 적용을 통한 생산성 40% 향상 도모.
    """)
    st.table(pd.DataFrame({"구분": ["배치 전략", "경로 로직", "물동량 비중"], "AS-IS": ["Random (무작위)", "First-In-First-Out", "상위 20% 품목이 후방 배치"]}))

# [STEP 2. AS-IS 동선 측정]
elif st.session_state['current_step'] == 1:
    st.header("2️⃣ AS-IS: 비최적화 동선 분석")
    st.warning("💡 **가이드:** 설비 배치와 경로 최적화가 없는 상태의 극심한 '동선 낭비'를 확인하세요.")
    
    df_asis = get_data('AS-IS', 35)
    dist_asis = np.sqrt(np.diff(df_asis['X'])**2 + np.diff(df_asis['Y'])**2).sum()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_warehouse(ax, "AS-IS")
        ax.plot(df_asis['X'], df_asis['Y'], color='#ff4b4b', alpha=0.7, linewidth=1.2, marker='o', markersize=3)
        st.pyplot(fig)
    with c2:
        st.metric("AS-IS 이동 거리", f"{dist_asis:.2f} m")
        st.error("**관찰 결과:**\n작업자가 Zone C(빨간 구역)를 수차례 반복 왕복하며, 선들이 복잡하게 얽히는 전형적인 비효율 동선을 보임.")

# [STEP 3. TO-BE 시뮬레이션]
elif st.session_state['current_step'] == 2:
    st.header("3️⃣ TO-BE: 설비 재배치 및 경로 최적화")
    st.success("💡 **가이드:** 변수를 조절한 후 '시뮬레이션 시작'을 누르세요. 배치가 바뀌어도 경로 알고리즘이 없으면 큰 효과가 없음을 인지해야 합니다.")
    
    with st.expander("🛠️ 시뮬레이션 파라미터 설정", expanded=True):
        v1, v2 = st.columns(2)
        u_count = v1.slider("피킹 물량", 10, 100, 45)
        u_ratio = v2.slider("인기 품목 비중 (%)", 10, 90, 80) / 100

    if st.button("▶️ 시뮬레이션 시작"):
        st.session_state['sim_done'] = False
        df_tobe = get_data('TO-BE', u_count, u_ratio)
        plot_spot = st.empty()
        
        for i in range(2, len(df_tobe)+1):
            fig, ax = plt.subplots(figsize=(10, 6))
            draw_warehouse(ax, "TO-BE")
            path = df_tobe.iloc[:i]
            ax.plot(path['X'], path['Y'], color='#00c853', alpha=0.8, linewidth=2, marker='o', markersize=4)
            plot_spot.pyplot(fig)
            time.sleep(0.01)
            plt.close()
        st.session_state['sim_done'] = True
        st.session_state['final_dist_t'] = np.sqrt(np.diff(df_tobe['X'])**2 + np.diff(df_tobe['Y'])**2).sum()
        st.rerun()

    if st.session_state.get('sim_done'):
        st.metric("TO-BE 예상 이동 거리", f"{st.session_state['final_dist_t']:.2f} m")
        st.info("결과: Zone A 집중 배치와 S-Shape 정렬을 통해 동선이 훨씬 간결해졌습니다.")

# [STEP 4. 최종 개선 리포트]
elif st.session_state['current_step'] == 3:
    st.header("4️⃣ 종합 분석 결과 및 최종 결론")
    st.info("💡 **가이드:** 정적인 두 데이터의 비교를 통해 설비 배치의 중요성을 최종 확정합니다.")
    
    # 비교 데이터 (동일 조건)
    d_a = get_data('AS-IS', 45, 0.8); dist_a = np.sqrt(np.diff(d_a['X'])**2 + np.diff(d_a['Y'])**2).sum()
    d_t = get_data('TO-BE', 45, 0.8); dist_t = np.sqrt(np.diff(d_t['X'])**2 + np.diff(d_t['Y'])**2).sum()
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.subheader("❌ AS-IS: 무작위 배치")
        fig_a, ax_a = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_a, "AS-IS")
        ax_a.plot(d_a['X'], d_a['Y'], color='#ff4b4b', alpha=0.5)
        st.pyplot(fig_a)
        st.markdown(f"""
        **비효율 진단:**
        물품의 속성(빈도)을 고려하지 않은 설비 배치로 인해 작업자의 **'공주행(Empty Travel)'**이 극대화되었습니다. 
        또한 최적화된 경로 알고리즘 없이 주문 순서대로 이동함에 따라 불필요한 역행과 중첩이 반복되는 구조입니다.
        - 측정 거리: **{dist_a:.1f}m**
        """)
        
    with res_col2:
        st.subheader("✅ TO-BE: 최적화 배치")
        fig_t, ax_t = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_t, "TO-BE")
        ax_t.plot(d_t['X'], d_t['Y'], color='#00c853', alpha=0.7)
        st.pyplot(fig_t)
        st.markdown(f"""
        **개선 성과:**
        ABC Slotting 전략에 따라 인기 품목을 전진 배치하고, S-Shape 알고리즘을 통해 **'원웨이(One-way) 피킹'**에 가까운 동선을 확보했습니다. 
        이는 단순히 거리를 줄이는 것을 넘어 작업자의 리듬감을 유지하고 처리량을 증대시키는 결과로 이어집니다.
        - 예상 거리: **{dist_t:.1f}m** (약 {((dist_a-dist_t)/dist_a*100):.1f}% 개선)
        """)

    st.divider()
    if st.button("🔄 분석 프로세스 다시 시작하기"):
        st.session_state['current_step'] = 0
        st.session_state['sim_done'] = False
        st.rerun()
