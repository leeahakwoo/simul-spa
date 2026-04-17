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
        # AS-IS: 인기 품목이 먼 곳(Zone C)에 배치된 최악의 상황 가정
        x_high = np.random.randint(70, 95, size=a_count)
        x_low = np.random.randint(10, 40, size=c_count)
        x = np.concatenate([x_high, x_low])
        y = np.random.randint(10, 90, size=count)
        p = np.random.permutation(len(x))
        x, y = x[p], y[p]
    else:
        # TO-BE: 인기 품목이 가까운 곳(Zone A)에 배치되고 경로 정렬
        x_high = np.random.randint(10, 40, size=a_count)
        x_low = np.random.randint(70, 95, size=c_count)
        x = np.concatenate([x_high, x_low])
        y = np.random.randint(10, 90, size=count)
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
        
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

def draw_warehouse(ax, mode, show_items=True):
    ax.set_facecolor('#f8f9fa')
    zones = [(15, "Zone A (입구)", "#d1e7dd"), (45, "Zone B (중앙)", "#fff3cd"), (75, "Zone C (후방)", "#f8d7da")]
    for sx, label, color in zones:
        ax.add_patch(patches.Rectangle((sx-5, 5), 25, 90, facecolor=color, alpha=0.3))
        ax.text(sx+5, 95, label, ha='center', fontweight='bold', fontsize=10)
    
    for sx in [15, 45, 75]:
        for sy in range(15, 85, 20):
            ax.add_patch(patches.Rectangle((sx, sy), 10, 10, facecolor='#6c757d', alpha=0.4))
            if show_items and mode == "TO-BE" and sx == 15:
                ax.text(sx+5, sy+5, "인기", color='green', fontsize=8, ha='center', va='center', fontweight='bold')
    ax.scatter(0, 0, c='blue', s=150, marker='s', label='Dock')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)

# --- 2. 메인 화면 구성 ---
st.title("📦 공정 선택과 설비 배치 최적화 프로젝트")
st.markdown("---")

step_names = ["Step 1. 배경 및 진단", "Step 2. AS-IS 동선 분석", "Step 3. TO-BE 시뮬레이션", "Step 4. 최종 개선 리포트"]
selected_tab = st.radio("분석 단계", step_names, index=st.session_state['current_step'], horizontal=True)
st.session_state['current_step'] = step_names.index(selected_tab)

# [STEP 1. 배경 및 진단]
if st.session_state['current_step'] == 0:
    st.header("1️⃣ 연구 배경 및 현재 상태 진단")
    st.info("💡 **가이드:** 물류센터의 비효율 원인을 파악하고 분석 가설을 수립합니다.")
    col_t, col_d = st.columns(2)
    with col_t:
        st.markdown("#### 🧐 현상 파악\n- 출고 물동량 대비 피킹 생산성 저하\n- 작업자의 보행 이동 거리 과다 발생")
    with col_d:
        st.write("#### 📊 공정 진단 데이터")
        st.table(pd.DataFrame({"항목": ["대상", "방식"], "내용": ["오더 피킹", "Random Slotting"]}))
    if st.button("다음 단계로 ➡️"):
        st.session_state['current_step'] = 1
        st.rerun()

# [STEP 2. AS-IS 동선 분석]
elif st.session_state['current_step'] == 1:
    st.header("2️⃣ AS-IS 동선 분석: 스파게티 다이어그램")
    st.warning("💡 **가이드:** 현재의 무질서한 동선을 확인합니다.")
    df_asis = get_data('AS-IS', 30)
    dist_asis = np.sqrt(np.diff(df_asis['X'])**2 + np.diff(df_asis['Y'])**2).sum()
    c1, c2 = st.columns([2, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_warehouse(ax, "AS-IS")
        ax.plot(df_asis['X'], df_asis['Y'], color='#ff4b4b', alpha=0.7, linewidth=1.2, marker='o', markersize=3)
        st.pyplot(fig)
    with c2:
        st.metric("AS-IS 이동 거리", f"{dist_asis:.2f} m")
        if st.button("개선 시뮬레이션 단계로 ➡️"):
            st.session_state['current_step'] = 2
            st.rerun()

# [STEP 3. TO-BE 시뮬레이션]
elif st.session_state['current_step'] == 2:
    st.header("3️⃣ 설비 배치 변경 시뮬레이션 (TO-BE)")
    st.success("💡 **가이드:** 사용자가 직접 변수를 조절하여 최적화 효과를 테스트할 수 있습니다.")
    
    # --- 사용자 변수 입력창 ---
    with st.expander("🛠️ 시뮬레이션 변수 설정", expanded=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            user_count = st.slider("피킹 총 물량 (건)", 10, 100, 40)
        with col_v2:
            user_a_ratio = st.slider("인기 품목(A-Class) 비중 (%)", 10, 90, 80) / 100

    sim_btn = st.button("▶️ 시뮬레이션 시작")
    
    df_tobe = get_data('TO-BE', user_count, user_a_ratio)
    dist_tobe = np.sqrt(np.diff(df_tobe['X'])**2 + np.diff(df_tobe['Y'])**2).sum()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        plot_spot = st.empty()
        if sim_btn:
            st.session_state['sim_done'] = False
            for i in range(2, len(df_tobe)+1):
                fig, ax = plt.subplots(figsize=(10, 6))
                draw_warehouse(ax, "TO-BE")
                path = df_tobe.iloc[:i]
                ax.plot(path['X'], path['Y'], color='#00c853', alpha=0.8, linewidth=2, marker='o', markersize=4)
                plot_spot.pyplot(fig)
                time.sleep(0.01)
                plt.close()
            st.session_state['sim_done'] = True
        else:
            # 시뮬레이션 전 대기 화면
            fig, ax = plt.subplots(figsize=(10, 6))
            draw_warehouse(ax, "TO-BE")
            plot_spot.pyplot(fig)

    with c2:
        if st.session_state.get('sim_done'):
            st.metric("TO-BE 예상 이동 거리", f"{dist_tobe:.2f} m")
            st.info(f"선택한 조건({user_count}건, A비중 {user_a_ratio*100:.0f}%)에서 최적의 동선이 생성되었습니다.")
            if st.button("마지막 단계로: 결과 비교 ➡️"):
                st.session_state['current_step'] = 3
                st.rerun()

# [STEP 4. 최종 개선 리포트]
elif st.session_state['current_step'] == 3:
    st.header("4️⃣ 최종 분석 결과 및 설비 배치 확정안")
    st.info("💡 **가이드:** AS-IS와 TO-BE의 최종 결과를 정적으로 비교하여 성과를 확인합니다.")
    
    # 비교를 위한 기본 데이터 (고정값)
    d_a = get_data('AS-IS', 40, 0.8); dist_a = np.sqrt(np.diff(d_a['X'])**2 + np.diff(d_a['Y'])**2).sum()
    d_t = get_data('TO-BE', 40, 0.8); dist_t = np.sqrt(np.diff(d_t['X'])**2 + np.diff(d_t['Y'])**2).sum()
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.subheader("❌ AS-IS (최적화 전)")
        fig_a, ax_a = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_a, "AS-IS", show_items=False)
        ax_a.plot(d_a['X'], d_a['Y'], color='#ff4b4b', alpha=0.5)
        st.pyplot(fig_a)
        st.markdown(f"""
        **현상 분석:** 무작위 배치로 인해 작업자가 전 구역을 중복 왕복하며 동선이 심하게 꼬여 있습니다.  
        이는 피킹 작업의 리드타임을 불필요하게 늘리고 작업 피로도를 가중시키는 핵심 요인입니다.  
        이동 거리: **{dist_a:.2f}m**
        """)
        
    with res_col2:
        st.subheader("✅ TO-BE (최적화 후)")
        fig_t, ax_t = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_t, "TO-BE")
        ax_t.plot(d_t['X'], d_t['Y'], color='#00c853', alpha=0.7)
        st.pyplot(fig_t)
        st.markdown(f"""
        **개선 효과:** 출고 빈도가 높은 상위 품목을 출고장 인접 구역(Zone A)에 배치하여 물리적 보행 거리를 원천적으로 제거했습니다.  
        정돈된 피킹 경로(S-Shape)를 통해 작업의 표준화와 예측 가능성을 확보하였습니다.  
        예상 거리: **{dist_t:.2f}m** (약 {((dist_a-dist_t)/dist_a*100):.1f}% 감소)
        """)

    st.divider()
    st.success("🏁 **종합 결론:** 본 프로젝트는 데이터 기반의 설비 배치(Slotting) 최적화가 물류 생산성에 기여하는 바를 정량적으로 증명하였습니다.")
    
    if st.button("🔄 처음으로 돌아가기"):
        st.session_state['current_step'] = 0
        st.session_state['sim_done'] = False
        st.rerun()
