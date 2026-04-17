import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
from PIL import Image, ImageDraw

# --- 페이지 설정 ---
st.set_page_config(layout="wide", page_title="Logistics Spaghetti Diagram Analysis")

# --- 세션 상태 초기화 ---
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 0
if 'sim_results' not in st.session_state:
    st.session_state['sim_results'] = None

# --- 1. 물류 센터 레이아웃 생성 엔진 (PIL 기반) ---
def create_warehouse_base():
    # 1200x800 해상도의 건물 바닥 생성
    width, height = 1200, 800
    base_img = Image.new('RGB', (width, height), '#F5F5F5')
    draw = ImageDraw.Draw(base_img)
    
    # 6개 통로(Aisle) 구획 및 랙 배치
    aisle_positions = [150, 300, 450, 600, 750, 900]
    for x in aisle_positions:
        # 통로 배경
        draw.rectangle([x-40, 50, x+40, 750], fill='#E0E0E0', outline='#BDBDBD')
        # 개별 랙(Rack) 표현
        for y in range(80, 750, 60):
            draw.rectangle([x-30, y, x+30, y+40], fill='#757575', outline='#424242')
            
    # 출고장 (Dock) 표시
    draw.rectangle([20, 350, 100, 450], fill='#1976D2', outline='#0D47A1')
    return base_img

# --- 2. 물류 데이터 및 라우팅 엔진 ---
def get_logistics_data(mode, count, a_ratio=0.8):
    np.random.seed(int(time.time()) % 1000)
    aisles = [150, 300, 450, 600, 750, 900]
    
    # ABC 등급별 가중치 적용 슬로팅
    grades = ['A', 'B', 'C', 'D']
    o_ratio = (1 - a_ratio)
    probs = [a_ratio, o_ratio * 0.6, o_ratio * 0.3, o_ratio * 0.1]
    
    selected_grades = np.random.choice(grades, size=count, p=probs)
    items = []
    for g in selected_grades:
        if mode == 'AS-IS':
            # 무질서 배치: 인기 품목(A)이 후방에 위치할 확률 높음
            x = np.random.choice(aisles[4:]) if g == 'A' else np.random.choice(aisles)
        else:
            # 최적화 배치: ABC Slotting 기반 전진 배치
            if g == 'A': x = np.random.choice(aisles[:2])
            elif g == 'B': x = np.random.choice(aisles[2:4])
            else: x = np.random.choice(aisles[4:])
        y = np.random.randint(100, 700)
        items.append({'x': x, 'y': y, 'grade': g})
    return pd.DataFrame(items)

def calculate_ie_metrics(df, mode):
    """산업공학 관점의 동선 지표 산출"""
    if mode == 'TO-BE':
        # S-Shape 라우팅 정렬
        sorted_df = df.sort_values(by=['x', 'y']).reset_index(drop=True)
        points = sorted_df[['x', 'y']].values
    else:
        points = df[['x', 'y']].values
        
    full_path = np.vstack([[60, 400], points, [60, 400]])
    
    # 맨해튼 거리 및 역행 분석
    dist = 0
    backtracking = 0
    for i in range(len(full_path) - 1):
        dist += abs(full_path[i][0] - full_path[i+1][0]) + abs(full_path[i][1] - full_path[i+1][1])
        if mode == 'AS-IS' and full_path[i+1][0] < full_path[i][0]:
            backtracking += 1
            
    return full_path, dist, backtracking

# --- 3. 대시보드 인터페이스 ---
st.title("🎓 Graduate Project: Warehouse Spaghetti Diagram Analysis")
st.markdown("---")

# 상단 네비게이션 가이드
nav_cols = st.columns([1, 4, 1])
with nav_cols[0]:
    if st.session_state['current_step'] > 0:
        if st.button("⬅️ PREV"): st.session_state['current_step'] -= 1; st.rerun()
with nav_cols[2]:
    if st.session_state['current_step'] < 3:
        if st.button("NEXT ➡️"): st.session_state['current_step'] += 1; st.rerun()

# --- 단계별 콘텐츠 ---

# [STEP 1] 배경 및 가설 수립
if st.session_state['current_step'] == 0:
    st.header("1️⃣ 배경: 운영 가변성과 낭비의 파악")
    st.info("💡 **가이드:** 현재 물류센터의 레이아웃과 데이터가 어떻게 상충하고 있는지 진단합니다.")
    
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("""
        #### 🧐 현상 진단
        - **무작위 적치(Random Slotting):** 출고 빈도 데이터와 무관한 설비 배치로 보행 거리 급증.
        - **스파게티 현상:** 작업자의 동선이 얽히고설켜 동일 통로 재진입이 반복되는 상태.
        
        #### 🎯 연구 가설
        "품목 빈도 기반 **ABC 슬로팅**과 **S-Shape 라우팅**의 결합은 총 이동 거리를 최소 50% 이상 단축할 것이다."
        """)
    with col_r:
        st.image(create_warehouse_base(), caption="Base Warehouse Layout (6 Aisles, 1 Dock)")

# [STEP 2] AS-IS 분석
elif st.session_state['current_step'] == 1:
    st.header("2️⃣ AS-IS: 비최적화 공정의 스파게티 다이어그램")
    st.warning("💡 **가이드:** 빨간색 선이 복잡하게 얽힌 정도를 통해 설비 배치 실패의 심각성을 확인하세요.")
    
    df_a = get_logistics_data('AS-IS', 35)
    path_a, dist_a, back_a = calculate_ie_metrics(df_a, 'AS-IS')
    
    c1, c2 = st.columns([2, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(create_warehouse_base())
        ax.plot(path_a[:,0], path_a[:,1], color='#FF5252', alpha=0.7, linewidth=2, marker='o', markersize=5, label='AS-IS Trace')
        ax.legend(); ax.axis('off')
        st.pyplot(fig)
    with c2:
        st.write("#### 📈 AS-IS 지표")
        st.metric("총 이동 거리 (Manhattan)", f"{dist_a:,} px")
        st.metric("역행(Backtracking) 횟수", f"{back_a} 회")
        st.error("**원인 분석:** 통로 5, 6번에 집중된 주문으로 인한 장거리 공주행 발생.")

# [STEP 3] TO-BE 시뮬레이션
elif st.session_state['current_step'] == 2:
    st.header("3️⃣ TO-BE: 알고리즘 기반 최적화 시뮬레이션")
    st.success("💡 **가이드:** ABC 가중치를 조절한 후 몬테카를로 시뮬레이션을 통해 통계적 개선 효과를 산출합니다.")
    
    with st.expander("🛠️ 시뮬레이션 파라미터 설정", expanded=True):
        p_count = st.slider("주문 물량(Count)", 20, 150, 50)
        a_ratio = st.slider("A등급 주문 비중(%)", 50, 95, 80) / 100
    
    if st.button("▶️ 시뮬레이션 실행"):
        results = []
        for _ in range(30):
            d = get_logistics_data('TO-BE', p_count, a_ratio)
            _, dist, _ = calculate_ie_metrics(d, 'TO-BE')
            results.append(dist)
        st.session_state['sim_results'] = {'mean': np.mean(results), 'std': np.std(results)}
        st.rerun()

    if st.session_state['sim_results']:
        res = st.session_state['sim_results']
        st.metric("평균 예상 이동 거리 (TO-BE)", f"{res['mean']:.1f} px", f"±{res['std']:.1f} (편차)")
    
    df_t = get_logistics_data('TO-BE', p_count, a_ratio)
    path_t, _, _ = calculate_ie_metrics(df_t, 'TO-BE')
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    ax2.imshow(create_warehouse_base())
    ax2.plot(path_t[:,0], path_t[:,1], color='#4CAF50', linewidth=2.5, marker='o', label='Optimized Route')
    ax2.legend(); ax2.axis('off')
    st.pyplot(fig2)

# [STEP 4] 최종 결과 및 제언
elif st.session_state['current_step'] == 3:
    st.header("4️⃣ 종합 성과 보고 및 최종 제언")
    
    # 최종 대조군 생성
    d_a = get_logistics_data('AS-IS', 50, 0.8)
    p_a, dist_a, _ = calculate_ie_metrics(d_a, 'AS-IS')
    d_t = get_logistics_data('TO-BE', 50, 0.8)
    p_t, dist_t, _ = calculate_ie_metrics(d_t, 'TO-BE')
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.subheader("❌ AS-IS (무질서 배치)")
        fig_f1, ax_f1 = plt.subplots(figsize=(10, 7))
        ax_f1.imshow(create_warehouse_base())
        ax_f1.plot(p_a[:,0], p_a[:,1], color='#FF5252', alpha=0.5, linewidth=1.2)
        ax_f1.axis('off'); st.pyplot(fig_f1)
        st.markdown(f"**이동 거리:** {dist_a:,} px  \n**분석:** 높은 무질서도(Entropy)를 보임.")
        
    with col_f2:
        st.subheader("✅ TO-BE (최적화 배치)")
        fig_f2, ax_f2 = plt.subplots(figsize=(10, 7))
        ax_f2.imshow(create_warehouse_base())
        ax_f2.plot(p_t[:,0], p_t[:,1], color='#4CAF50', alpha=0.7, linewidth=1.5)
        ax_f2.axis('off'); st.pyplot(fig_f2)
        st.markdown(f"**이동 거리:** {dist_t:,} px  \n**분석:** 일방통행 기반 동선 안정화.")

    st.divider()
    st.subheader("📝 최종 제언")
    st.success(f"최적화 결과, 이동 거리가 **약 {((dist_a-dist_t)/dist_a*100):.1f}% 단축**되었습니다. "
               "이는 단순한 이동 거리의 감소뿐만 아니라 작업자의 피로도 감소와 처리량 증대로 이어질 것입니다.")
    if st.button("🔄 처음으로 돌아가기"):
        st.session_state['current_step'] = 0
        st.rerun()
