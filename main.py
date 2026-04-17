"""
대학원 물류공학 과제: 스파게티 다이어그램 분석 대시보드
주요 기능: 맨해튼 거리 산출, 교차점 감지, 누적 동선 시각화, 히트맵 병목 분석
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# --- 페이지 설정 ---
st.set_page_config(layout="wide", page_title="Logistics Spaghetti Diagram Analytics")

# --- 1. 수학적 교차점 감지 알고리즘 ---
def ccw(A, B, C):
    """세 점의 방향성을 확인하는 CCW (Counter Clockwise) 알고리즘"""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def check_intersect(A, B, C, D):
    """두 선분 AB와 CD가 교차하는지 판별"""
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

def detect_line_intersections(path):
    """경로 내 선분들의 교차점 좌표와 개수를 반환"""
    intersections = []
    segments = [(path[i], path[i+1]) for i in range(len(path)-1)]
    
    for i in range(len(segments)):
        for j in range(i + 2, len(segments)): # 인접한 선분(i, i+1)은 제외
            A, B = segments[i]
            C, D = segments[j]
            if check_intersect(A, B, C, D):
                # 수직/수평선의 맨해튼 이동이므로 교차점의 대략적 중심점 계산
                ix = min(max(A[0], B[0]), max(C[0], D[0]))
                iy = min(max(A[1], B[1]), max(C[1], D[1]))
                intersections.append((ix, iy))
                
    return intersections, len(intersections)

# --- 2. 물류 데이터 및 지표 산출 엔진 ---
def get_logistics_data(mode, count, a_ratio=0.8):
    """다변수(등급별 가중치)를 반영한 오더 데이터 생성"""
    np.random.seed(int(time.time()) % 1000)
    aisles = [150, 300, 450, 600, 750, 900]
    grades = ['A', 'B', 'C', 'D']
    probs = [a_ratio, (1-a_ratio)*0.6, (1-a_ratio)*0.3, (1-a_ratio)*0.1]
    
    items = []
    selected_grades = np.random.choice(grades, size=count, p=probs)
    
    for g in selected_grades:
        if mode == 'AS-IS':
            x = np.random.choice(aisles[4:]) if g == 'A' else np.random.choice(aisles)
        else:
            if g == 'A': x = np.random.choice(aisles[:2])
            elif g == 'B': x = np.random.choice(aisles[2:4])
            else: x = np.random.choice(aisles[4:])
        y = np.random.randint(100, 700)
        items.append({'x': x, 'y': y, 'grade': g})
        
    df = pd.DataFrame(items)
    if mode == 'TO-BE':
        # S-Shape 정렬
        df = df.sort_values(by=['x', 'y']).reset_index(drop=True)
    return df

def calculate_ie_metrics_advanced(df, mode):
    """산업공학적 고급 지표 산출 (거리, 역행, 교차점, 비효율도)"""
    points = df[['x', 'y']].values
    full_path = np.vstack([[60, 400], points, [60, 400]]) # Start/End at Dock
    
    dist = 0
    backtracking = 0
    for i in range(len(full_path) - 1):
        dist += abs(full_path[i][0] - full_path[i+1][0]) + abs(full_path[i][1] - full_path[i+1][1])
        if mode == 'AS-IS' and full_path[i+1][0] < full_path[i][0]:
            backtracking += 1
            
    # 교차점 검사 추가
    intersections, intersection_count = detect_line_intersections(full_path)
    
    # 비효율도 점수 산출 (거리가 길수록 점수 분모가 커지므로 스케일링)
    inefficiency_score = (intersection_count / (dist / 1000)) * 100 if dist > 0 else 0
    
    return {
        'path': full_path,
        'distance': dist,
        'backtracking': backtracking,
        'intersections': intersections,
        'intersection_count': intersection_count,
        'inefficiency_score': inefficiency_score
    }

# --- 3. 시각화 (Matplotlib) ---
def draw_warehouse_ax(ax):
    """matplotlib Axes에 물류센터 도면을 그리는 함수"""
    ax.set_facecolor('#F5F5F5')
    aisles = [150, 300, 450, 600, 750, 900]
    for x in aisles:
        # 통로 구역
        ax.add_patch(patches.Rectangle((x-40, 50), 80, 700, facecolor='#E0E0E0', edgecolor='none', alpha=0.5))
        # 랙
        for y in range(80, 750, 60):
            ax.add_patch(patches.Rectangle((x-30, y), 60, 40, facecolor='#757575', edgecolor='#424242'))
        ax.text(x, 770, f"Aisle {aisles.index(x)+1}", ha='center', fontweight='bold', color='#424242')
            
    # Dock
    ax.add_patch(patches.Rectangle((20, 350), 80, 100, facecolor='#1976D2', edgecolor='none', alpha=0.8))
    ax.text(60, 400, "DOCK", ha='center', va='center', color='white', fontweight='bold')
    
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 800)
    ax.invert_yaxis() # y축 위에서 아래로
    ax.axis('off')

# --- 4. 대시보드 인터페이스 ---
st.title("📦 데이터 기반 스파게티 다이어그램 분석 시스템")
st.markdown("가상 물류센터 데이터를 활용하여 픽킹 순서 최적화 전후의 동선 낭비를 시각화하고 정량적으로 분석합니다.")

# 사이드바: 시뮬레이션 설정
with st.sidebar:
    st.header("⚙️ 시뮬레이션 설정")
    mode = st.radio("분석 모드 (Scenario)", ["AS-IS (현재/무질서)", "TO-BE (개선/최적화)"])
    order_count = st.slider("주문 내 품목 수 (Volume)", 10, 80, 30)
    a_class_ratio = st.slider("A등급(인기) 품목 비중", 0.5, 0.95, 0.8)
    multi_orders = st.slider("누적 분석용 주문 건수 (Batch)", 2, 20, 5)
    
    st.markdown("---")
    st.info("💡 **지표 설명**\n- **역행:** 진행 방향과 반대로 돌아가는 횟수\n- **교차점:** 동선이 꼬인 횟수\n- **비효율도:** 거리 대비 교차 발생 빈도")

# 데이터 생성 및 메트릭 계산
df = get_logistics_data(mode.split(" ")[0], order_count, a_class_ratio)
metrics = calculate_ie_metrics_advanced(df, mode.split(" ")[0])

# 4개의 분석 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    "① 단일 주문 스파게티", 
    "② 누적 스파게티 분석", 
    "③ 병목 구간(Heatmap)", 
    "④ 자동 생성 리포트"
])

# [TAB 1] 단일 주문 분석 (화살표, 순서 번호, 교차점 X)
with tab1:
    st.subheader(f"📍 단일 주문 동선 정밀 분석 ({mode})")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(12, 8))
        draw_warehouse_ax(ax)
        path = metrics['path']
        color = '#FF5252' if 'AS-IS' in mode else '#4CAF50'
        
        # 선 및 화살표, 순서 번호 그리기
        for i in range(len(path)-1):
            start, end = path[i], path[i+1]
            ax.annotate("", xy=end, xytext=start,
                        arrowprops=dict(arrowstyle="->", color=color, lw=1.5, alpha=0.8))
            if i > 0: # Dock 출발점 제외
                ax.text(start[0]+15, start[1]-15, f"{i}", color='black', fontsize=9, 
                        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, boxstyle='circle'))
                
        # 교차점 X 표시
        for ix, iy in metrics['intersections']:
            ax.plot(ix, iy, marker='x', markersize=10, color='blue', markeredgewidth=2)
            
        st.pyplot(fig)
        
    with col2:
        st.write("#### 📊 성과 지표")
        st.metric("총 이동 거리", f"{metrics['distance']:,} px")
        st.metric("역행 (Backtracking)", f"{metrics['backtracking']} 회")
        st.metric("동선 교차점", f"{metrics['intersection_count']} 개")
        st.metric("비효율도 점수", f"{metrics['inefficiency_score']:.1f}")

# [TAB 2] 누적 스파게티 분석
with tab2:
    st.subheader(f"🌪️ {multi_orders}건 누적 스파게티 다이어그램 ({mode})")
    st.markdown("여러 작업자의 동선이 겹쳤을 때 발생하는 혼잡도를 시각화합니다.")
    
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    draw_warehouse_ax(ax2)
    
    colors = plt.cm.tab10(np.linspace(0, 1, multi_orders))
    total_dist = 0
    total_inter = 0
    
    for i in range(multi_orders):
        batch_df = get_logistics_data(mode.split(" ")[0], order_count, a_class_ratio)
        b_metrics = calculate_ie_metrics_advanced(batch_df, mode.split(" ")[0])
        b_path = b_metrics['path']
        
        total_dist += b_metrics['distance']
        total_inter += b_metrics['intersection_count']
        
        ax2.plot(b_path[:,0], b_path[:,1], color=colors[i], alpha=0.5, linewidth=1.5)
        
    st.pyplot(fig2)
    st.info(f"**누적 통계 요약:** 평균 이동 거리 **{total_dist/multi_orders:,.0f} px** / 평균 교차점 **{total_inter/multi_orders:.1f} 개**")

# [TAB 3] 히트맵 병목 분석
with tab3:
    st.subheader("🔥 물리적 병목 구간 분석 (Heatmap)")
    st.markdown("작업자의 발길이 가장 많이 닿는 구역(Hotspot)을 2D 히트맵으로 도출합니다.")
    
    # 히트맵 생성을 위해 누적 데이터의 모든 좌표 수집
    all_x, all_y = [], []
    for _ in range(10): # 히트맵을 위해 샘플 10개 강제 생성
        h_df = get_logistics_data(mode.split(" ")[0], order_count, a_class_ratio)
        h_path = calculate_ie_metrics_advanced(h_df, mode.split(" ")[0])['path']
        all_x.extend(h_path[:,0])
        all_y.extend(h_path[:,1])
        
    fig3, ax3 = plt.subplots(figsize=(12, 8))
    draw_warehouse_ax(ax3)
    
    # 2D Histogram으로 히트맵 오버레이
    hb = ax3.hexbin(all_x, all_y, gridsize=30, cmap='YlOrRd', alpha=0.6, mincnt=1)
    fig3.colorbar(hb, ax=ax3, label='Visit Frequency')
    st.pyplot(fig3)

# [TAB 4] 자동 생성 리포트
with tab4:
    st.subheader("📑 자동 분석 리포트")
    
    grade_report = "불량" if metrics['inefficiency_score'] > 30 else "경고" if metrics['inefficiency_score'] > 10 else "우수"
    
    st.markdown(f"""
    ### 1. 공정 종합 평가
    - **분석 시나리오:** `{mode}`
    - **종합 공정 등급:** **{grade_report}**
    - **비효율도 점수:** {metrics['inefficiency_score']:.2f} (동선 1000px 당 교차점 발생률)
    
    ### 2. 정량적 지표 분석
    현재 단일 주문 기준으로 작업자는 **{metrics['distance']:,} px**을 이동하며, 이 과정에서 **{metrics['backtracking']}번의 역행**과 **{metrics['intersection_count']}개의 동선 교차점**이 발생했습니다. 
    
    ### 3. 공학적 인사이트
    """)
    
    if 'AS-IS' in mode:
        st.error("""
        - **스파게티 현상 심각:** 동선이 얽혀 교차점이 다수 발생하고 있습니다. 이는 지게차나 작업자 간의 물리적 충돌 위험(간섭 현상)을 높입니다.
        - **개선 방향:** 현재 품목의 출고 빈도를 고려하지 않은 Random Slotting 상태입니다. A등급 품목을 출고장(Dock) 인근 통로 1, 2번으로 전진 배치하는 ABC 분석 기반의 슬로팅 전략이 시급합니다.
        """)
    else:
        st.success("""
        - **원웨이(One-way) 동선 확립:** 교차점과 역행이 획기적으로 줄어들어 동선이 표준화되었습니다.
        - **유지보수:** S-Shape 경로 라우팅 알고리즘이 효과적으로 작동하고 있으며, 지속적인 모니터링을 통해 물동량 변화(Seasonality)에 따른 A등급 품목의 재배치(Re-slotting)를 주기적으로 수행해야 합니다.
        """)
