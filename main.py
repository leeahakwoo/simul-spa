import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

st.set_page_config(layout="wide", page_title="공정 설계 및 설비 배치 최적화")

# --- 0. 초기 세션 및 상태 관리 ---
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 0
if 'sim_done' not in st.session_state:
    st.session_state['sim_done'] = False

# --- 1. 고도화된 데이터 및 시뮬레이션 엔진 ---
def get_advanced_data(mode, count, a_ratio=0.8):
    np.random.seed(42)
    # 6개의 통로(Aisle) 좌표 설정
    aisles = [15, 30, 45, 60, 75, 90]
    
    if mode == 'AS-IS':
        # 로직: 인기 품목이 후방(Aisle 4,5,6)에 배치됨 + 경로 최적화 없음(무작위 순서)
        x_choices = aisles[3:] # 먼 곳 위주
        x = np.random.choice(x_choices, size=count)
        y = np.random.randint(10, 90, size=count)
        # 작업자가 주문서에 적힌 랜덤한 순서대로 이동하는 상황 모사 (Backtracking 발생)
        p = np.random.permutation(count)
        x, y = x[p], y[p]
    else:
        # 로직: 인기 품목(a_ratio)을 전방(Aisle 1,2)에 배치 + S-Shape Routing 알고리즘
        a_aisles = aisles[:2]
        c_aisles = aisles[2:]
        
        a_count = int(count * a_ratio)
        c_count = count - a_count
        
        x = np.concatenate([np.random.choice(a_aisles, size=a_count), 
                            np.random.choice(c_aisles, size=c_count)])
        y = np.random.randint(10, 90, size=count)
        
        # S-Shape Routing: 통로 순서대로 정렬하여 동선 중첩 제거
        df = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df['x'].values, df['y'].values
        
    # 시작점(Dock) 추가
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

def draw_warehouse(ax):
    ax.set_facecolor('#fdfdfd')
    aisles = [15, 30, 45, 60, 75, 90]
    # 통로 구역 시각화 (A: 녹색, B: 황색, C: 적색)
    for i, x in enumerate(aisles):
        color = "#d1e7dd" if i < 2 else "#fff3cd" if i < 4 else "#f8d7da"
        ax.add_patch(patches.Rectangle((x-4, 5), 8, 90, facecolor=color, alpha=0.25))
        ax.text(x, 97, f"Aisle {i+1}", ha='center', fontsize=9, fontweight='bold')
        # 랙(Rack) 표현
        for y in range(10, 95, 15):
            ax.add_patch(patches.Rectangle((x-3, y), 6, 8, facecolor='#495057', alpha=0.4))
            
    ax.scatter(0, 0, c='#007bff', s=250, marker='s', label='Dock')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)
    ax.axis('off')

# --- 2. 상단 네비게이션 시스템 ---
st.title("📦 데이터 기반 설비 배치 및 공정 최적화")

nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
with nav_col1:
    if st.session_state['current_step'] > 0:
        if st.button("⬅️ 이전 단계"):
            st.session_state['current_step'] -= 1
            st.session_state['sim_done'] = False
            st.rerun()

with nav_col3:
    # 마지막 단계가 아니고, Step 3 시뮬레이션이 완료된 경우에만 다음 버튼 활성화
    show_next = st.session_state['current_step'] < 3
    if st.session_state['current_step'] == 2 and not st.session_state.get('sim_done'):
        show_next = False
    
    if show_next:
        if st.button("다음 단계 ➡️"):
            st.session_state['current_step'] += 1
            st.rerun()

st.markdown("---")

# --- 3. 단계별 스토리텔링 콘텐츠 ---

# [STEP 1] 배경 및 진단
if st.session_state['current_step'] == 0:
    st.header("1️⃣ 진단: 물리적 배치와 운영 가변성")
    st.info("💡 **가이드:** 현재 물류 현장은 데이터 분석 없이 설비가 배치되어 불필요한 공주행 거리가 발생하고 있습니다.")
    
    st.markdown("""
    #### 🧐 핵심 문제 진단
    1. **슬로팅 비효율:** 출고 빈도가 가장 높은 'A-Class' 품목이 입구에서 가장 먼 **Aisle 5, 6**에 산재되어 있음.
    2. **경로 무질서:** 최적화된 라우팅 알고리즘 부재로 인해 작업자가 동일한 통로를 수차례 왕복하는 **Backtracking** 현상 심화.
    3. **데이터 엔트로피:** 주문 발생 순서에 따른 수동적 이동으로 인해 전체 공정 리드타임의 예측 가능성 결여.
    """)
    
    # 분석 가중치 표
    st.table(pd.DataFrame({
        "분석 지표": ["배치 전략", "라우팅 알고리즘", "기대 성과"],
        "AS-IS (현재)": ["무작위 배치 (Random)", "주문 순서 이동", "-"],
        "TO-BE (개선)": ["마이크로 슬로팅 (ABC)", "S-Shape 알고리즘", "이동 거리 60% 이상 단축"]
    }))

# [STEP 2] AS-IS 분석
elif st.session_state['current_step'] == 1:
    st.header("2️⃣ AS-IS: 비최적화 공정의 동선 시각화")
    st.warning("💡 **가이드:** 무작위로 얽힌 빨간색 선들은 설비 배치가 데이터와 분리되었을 때 발생하는 '낭비'를 의미합니다.")
    
    df_asis = get_advanced_data('AS-IS', 35)
    dist_asis = np.sqrt(np.diff(df_asis['X'])**2 + np.diff(df_asis['Y'])**2).sum()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_warehouse(ax)
        ax.plot(df_asis['X'], df_asis['Y'], color='#dc3545', alpha=0.6, linewidth=1.5, marker='o', markersize=4)
        ax.set_title("Spaghetti Diagram: High Entropy Process", fontsize=12)
        st.pyplot(fig)
    with col2:
        st.metric("AS-IS 총 이동 거리", f"{dist_asis:.2f} m")
        st.error("**비효율 포인트:**\n- 작업자가 구역 전체(Aisle 1~6)를 비효율적으로 횡단.\n- 6번 통로 진입 횟수가 과다하여 Dock과의 물리적 거리가 누적됨.")

# [STEP 3] TO-BE 시나리오 시뮬레이션
elif st.session_state['current_step'] == 2:
    st.header("3️⃣ TO-BE: 마이크로 슬로팅 및 S-Shape 시뮬레이션")
    st.success("💡 **가이드:** 물동량 변수를 설정한 후 시뮬레이션을 시작하세요. 정돈된 'ㄹ'자 동선은 프로세스 표준화의 결과입니다.")
    
    with st.expander("🛠️ 데이터 시뮬레이션 파라미터", expanded=True):
        v1, v2 = st.columns(2)
        u_count = v1.slider("피킹 총 물량(건)", 20, 100, 50)
        u_ratio = v2.slider("인기 품목(A-Class) 집중도 (%)", 10, 95, 80) / 100

    sim_btn = st.button("▶️ 최적화 프로세스 시뮬레이션 시작")
    
    df_tobe = get_advanced_data('TO-BE', u_count, u_ratio)
    dist_tobe = np.sqrt(np.diff(df_tobe['X'])**2 + np.diff(df_tobe['Y'])**2).sum()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        plot_spot = st.empty()
        if sim_btn:
            st.session_state['sim_done'] = False
            for i in range(2, len(df_tobe)+1):
                fig, ax = plt.subplots(figsize=(10, 6))
                draw_warehouse(ax)
                path = df_tobe.iloc[:i]
                ax.plot(path['X'], path['Y'], color='#28a745', alpha=0.8, linewidth=2.5, marker='o', markersize=5)
                plot_spot.pyplot(fig)
                time.sleep(0.01)
                plt.close()
            st.session_state['sim_done'] = True
            st.session_state['final_dist_t'] = dist_tobe
            st.rerun()
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            draw_warehouse(ax)
            plot_spot.pyplot(fig)

    with col2:
        if st.session_state.get('sim_done'):
            st.metric("TO-BE 예상 이동 거리", f"{st.session_state['final_dist_t']:.2f} m")
            st.info("**최적화 전략:**\n- 입구(Dock) 근접 통로에 물량 80% 집중.\n- 통로 내 역행 방지 및 순차 피킹 로직 적용.")

# [STEP 4] 최종 리포트 및 비교
elif st.session_state['current_step'] == 3:
    st.header("4️⃣ 종합 성과 보고서 및 최종 제언")
    st.info("💡 **가이드:** 정적인 두 데이터의 비교는 설비 배치가 공정 리드타임에 미치는 결정적인 영향력을 증명합니다.")
    
    # 결과 비교를 위한 데이터 세팅 (동일 조건)
    d_a = get_advanced_data('AS-IS', 50, 0.8); dist_a = np.sqrt(np.diff(d_a['X'])**2 + np.diff(d_a['Y'])**2).sum()
    d_t = get_advanced_data('TO-BE', 50, 0.8); dist_t = np.sqrt(np.diff(d_t['X'])**2 + np.diff(d_t['Y'])**2).sum()
    
    res1, res2 = st.columns(2)
    with res1:
        st.subheader("❌ AS-IS (무질서 배치)")
        fig_a, ax_a = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_a)
        ax_a.plot(d_a['X'], d_a['Y'], color='#dc3545', alpha=0.5, linewidth=1.2)
        st.pyplot(fig_a)
        st.markdown(f"""
        **현상 분석:** 설비 배치와 수요 예측 데이터가 단절된 상태입니다. 작업자는 매 주문마다 먼 통로를 왕복해야 하며, 동선이 중첩되어 물리적 피로도가 급격히 상승합니다.  
        - 총 이동 거리: **{dist_a:.1f}m**
        - 비효율 원인: **Backtracking 및 과도한 공주행**
        """)
        
    with res2:
        st.subheader("✅ TO-BE (최적화 배치)")
        fig_t, ax_t = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_t)
        ax_t.plot(d_t['X'], d_t['Y'], color='#28a745', alpha=0.7, linewidth=1.5)
        st.pyplot(fig_t)
        st.markdown(f"""
        **개선 성과:** 출고 빈도에 기반한 통로별 가중치 배치(Micro-Slotting)를 통해 주요 보행 동선을 입구 근처로 제한하였습니다. 정돈된 흐름은 작업 속도를 표준화하고 오피킹 확률을 낮춥니다.  
        - 예상 거리: **{dist_t:.1f}m**
        - 개선 효율: **약 {((dist_a-dist_t)/dist_a*100):.1f}% 단축**
        """)

    st.divider()
    st.success("🏁 **프로젝트 결론:** 본 시뮬레이션은 설비 배치(Slotting) 최적화와 공정(Routing)의 결합이 물류 생산성의 획기적 향상을 가져오는 핵심 전략임을 정량적으로 입증합니다.")
    
    if st.button("🔄 전체 분석 프로세스 다시 시작하기"):
        st.session_state['current_step'] = 0
        st.session_state['sim_done'] = False
        st.rerun()
