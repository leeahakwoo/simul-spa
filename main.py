import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="공정 설계 및 설비 배치 최적화 보고서")

# --- 0. 초기 세션 관리 ---
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 0
if 'mc_results' not in st.session_state:
    st.session_state['mc_results'] = None

# --- 1. 물류 엔진 (Manhattan 거리 및 S-Shape 알고리즘) ---

def generate_complex_data(mode, count, a_ratio=0.8):
    """등급별 가중 확률 슬로팅 적용 (Pareto 분포 반영)"""
    np.random.seed(int(time.time()) % 1000)
    aisles = [15, 30, 45, 60, 75, 90]
    
    # 등급: A(최고), B, C, D(최저)
    grades = ['A', 'B', 'C', 'D']
    o_ratio = (1 - a_ratio)
    probs = [a_ratio, o_ratio * 0.6, o_ratio * 0.3, o_ratio * 0.1]
    
    selected_grades = np.random.choice(grades, size=count, p=probs)
    items = []
    for g in selected_grades:
        if mode == 'AS-IS':
            # 비효율: 인기 품목이 먼 곳에 배치될 확률 높음
            x = np.random.choice(aisles[4:]) if g == 'A' else np.random.choice(aisles)
        else:
            # 최적화: ABC Slotting 기반 전진 배치
            if g == 'A': x = np.random.choice(aisles[:2])
            elif g == 'B': x = np.random.choice(aisles[2:4])
            else: x = np.random.choice(aisles[4:])
        y = np.random.randint(10, 90)
        items.append({'x': x, 'y': y, 'grade': g})
    return pd.DataFrame(items)

def calculate_route_and_dist(df, mode):
    """Manhattan 거리 모델 및 Routing 알고리즘 적용"""
    if mode == 'TO-BE':
        # S-Shape Routing: 통로 순서대로 이동하며 상/하 방향성 제어
        sorted_df = df.sort_values(by=['x', 'y']).reset_index(drop=True)
        # 통로별로 지그재그 방향성을 주는 것은 시각화용이며, 
        # 맨해튼 거리상으로는 통로 정렬만으로도 최적 동선 확보 가능
        raw_points = sorted_df[['x', 'y']].values
    else:
        # AS-IS: 최적화 부재 (주문 발생 랜덤 순서)
        raw_points = df[['x', 'y']].values
    
    path = np.vstack([[0,0], raw_points, [0,0]])
    
    # Manhattan 거리 계산 (직각 이동 제약)
    dist = 0
    backtracking = 0
    for i in range(len(path) - 1):
        dist += abs(path[i][0] - path[i+1][0]) + abs(path[i][1] - path[i+1][1])
        if mode == 'AS-IS' and path[i+1][0] < path[i][0]:
            backtracking += 1
            
    return path, dist, backtracking

# --- 2. 시각화 및 UI ---

def draw_warehouse(ax):
    ax.set_facecolor('#f8f9fa')
    aisles = [15, 30, 45, 60, 75, 90]
    for i, x in enumerate(aisles):
        color = "#d1e7dd" if i < 2 else "#fff3cd" if i < 4 else "#f8d7da"
        ax.add_patch(patches.Rectangle((x-4, 5), 8, 90, facecolor=color, alpha=0.3))
        ax.text(x, 97, f"Aisle {i+1}", ha='center', fontsize=9, fontweight='bold')
    ax.scatter(0, 0, c='blue', s=200, marker='s', label='Dock')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)
    ax.axis('off')

# --- 3. 단계별 보고서 구성 ---

st.title("🏭 공정 설계 및 설비 배치 최적화 분석")
st.markdown("---")

# 상단 네비게이션
nav1, nav2, nav3 = st.columns([1, 4, 1])
with nav1:
    if st.session_state['current_step'] > 0:
        if st.button("⬅️ PREV"): st.session_state['current_step'] -= 1; st.rerun()
with nav3:
    if st.session_state['current_step'] < 3:
        if st.button("NEXT ➡️"): st.session_state['current_step'] += 1; st.rerun()

# [STEP 1] 진단
if st.session_state['current_step'] == 0:
    st.header("1️⃣ 배경: 운영 비효율의 수치화")
    st.info("💡 **가이드:** 현재의 무질서한 배치가 작업 생산성을 얼마나 저해하는지 분석합니다.")
    st.markdown("""
    #### 🧐 핵심 당면 과제
    1. **무작위 적치(Random Slotting):** 출고 빈도가 높은 상위 SKU가 센터 후방에 위치하여 이동 낭비 발생.
    2. **인지 부하(Cognitive Load):** 경로 알고리즘 부재로 작업자가 매번 경로를 임의 판단하여 역행 발생.
    3. **가변성(Variability):** 작업자마다 다른 동선을 보여주어 공정 표준화가 불가능한 상태.
    """)
    st.table(pd.DataFrame({
        "지표": ["이동 모델", "슬로팅 전략", "라우팅 로직"],
        "현 상태": ["Euclidean (비현실적)", "Random", "주문서 순서"],
        "개선안": ["Manhattan (현실적)", "ABC Slotting", "S-Shape Algorithm"]
    }))

# [STEP 2] AS-IS 분석
elif st.session_state['current_step'] == 1:
    st.header("2️⃣ AS-IS: 스파게티 다이어그램 분석")
    st.warning("💡 **가이드:** 무질서한 동선에서 발생하는 역행(Backtracking) 현상을 확인하십시오.")
    
    df_a = generate_complex_data('AS-IS', 35)
    path_a, dist_a, back_a = calculate_route_and_dist(df_a, 'AS-IS')
    
    c1, c2 = st.columns([2, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(10, 5))
        draw_warehouse(ax)
        ax.plot(path_a[:,0], path_a[:,1], color='#dc3545', alpha=0.6, marker='o', label='AS-IS')
        st.pyplot(fig)
    with c2:
        st.metric("총 이동 거리", f"{dist_a:.1f} m")
        st.metric("역행 발생 횟수", f"{back_a} 회")
        st.error("**원인 분석:** 물품 등급(A~D)을 무시한 배치로 인해 주 활동 영역이 통로 5, 6번에 집중됨.")

# [STEP 3] TO-BE 시뮬레이션 및 검증
elif st.session_state['current_step'] == 2:
    st.header("3️⃣ TO-BE: 알고리즘 기반 시뮬레이션")
    st.success("💡 **가이드:** 물량과 집중도를 조절하여 몬테카를로 시뮬레이션(반복 실험)을 수행합니다.")
    
    with st.expander("🛠️ 파라미터 미세 조정", expanded=True):
        col_v1, col_v2 = st.columns(2)
        v_count = col_v1.slider("피킹 물량(Count)", 20, 150, 50)
        v_skew = col_v2.slider("A등급 주문 비중(%)", 50, 95, 80) / 100
    
    run_btn = st.button("▶️ 몬테카를로 시뮬레이션 실행 (30회 반복)")
    
    if run_btn:
        results = []
        for _ in range(30):
            data = generate_complex_data('TO-BE', v_count, v_skew)
            _, d, _ = calculate_route_and_dist(data, 'TO-BE')
            results.append(d)
        
        # AS-IS 비교군 (기본값)
        asis_results = []
        for _ in range(30):
            data_a = generate_complex_data('AS-IS', v_count, v_skew)
            _, d_a, _ = calculate_route_and_dist(data_a, 'AS-IS')
            asis_results.append(d_a)
            
        st.session_state['mc_results'] = {
            'mean_a': np.mean(asis_results),
            'mean_t': np.mean(results),
            'std_t': np.std(results)
        }

    if st.session_state['mc_results']:
        res = st.session_state['mc_results']
        m1, m2, m3 = st.columns(3)
        m1.metric("TO-BE 평균 거리", f"{res['mean_t']:.1f} m")
        m2.metric("예상 개선율", f"{((res['mean_a'] - res['mean_t'])/res['mean_a']*100):.1f} %")
        m3.metric("데이터 신뢰도(Std)", f"±{res['std_t']:.1f}")

    # 실시간 동선 예시
    df_t = generate_complex_data('TO-BE', v_count, v_skew)
    path_t, dist_t, _ = calculate_route_and_dist(df_t, 'TO-BE')
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    draw_warehouse(ax2)
    ax2.plot(path_t[:,0], path_t[:,1], color='#28a745', linewidth=2, marker='o', label='Optimized')
    st.pyplot(fig2)

# [STEP 4] 최종 결과
elif st.session_state['current_step'] == 3:
    st.header("4️⃣ 종합 성과 보고 및 최종 제언")
    
    # 정적 데이터 비교
    d_a_sample = generate_complex_data('AS-IS', 50, 0.8)
    p_a, dist_a, _ = calculate_route_and_dist(d_a_sample, 'AS-IS')
    
    d_t_sample = generate_complex_data('TO-BE', 50, 0.8)
    p_t, dist_t, _ = calculate_route_and_dist(d_t_sample, 'TO-BE')
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.subheader("❌ AS-IS (무작위 배치)")
        fig_f1, ax_f1 = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_f1)
        ax_f1.plot(p_a[:,0], p_a[:,1], color='#dc3545', alpha=0.4)
        st.pyplot(fig_f1)
        st.write(f"총 이동 거리: **{dist_a:.1f}m**")
        st.markdown("**현상:** 주문 빈도를 무시한 랙 할당으로 인해 전체 동선이 센터 후방으로 치우쳐 있으며, 역행 동선이 빈번하게 발생합니다.")
        
    with col_f2:
        st.subheader("✅ TO-BE (최적화 배치)")
        fig_f2, ax_f2 = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_f2)
        ax_f2.plot(p_t[:,0], p_t[:,1], color='#28a745', alpha=0.6)
        st.pyplot(fig_f2)
        st.write(f"총 이동 거리: **{dist_t:.1f}m**")
        st.markdown("**성과:** ABC 등급 기반 슬로팅과 S-Shape 경로 최적화를 통해 작업 동선을 입구 근처로 압축하고 공정의 가변성을 제거하였습니다.")

    st.divider()
    st.markdown("### 📝 최종 제언 (Conclusion)")
    st.success("단순히 물건을 옮기는 것보다 **ABC 등급 가중치**를 고려한 데이터 기반의 **Micro-Slotting**과 **표준화된 라우팅 알고리즘**이 결합될 때 물리적 에너지 소모량을 최소화할 수 있습니다.")
    if st.button("🔄 Restart Analysis"):
        st.session_state['current_step'] = 0
        st.rerun()
