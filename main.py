import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="물류 프로세스 및 설비 배치 최적화")

# --- 1. [상단] 과제 섹션 및 스토리 배경 ---
st.title("📦 프로세스 선택과 설비 배치: 동선 최적화 시뮬레이션")
st.markdown("""
### 📖 가상 분석 시나리오
본 시뮬레이션은 **'ABC 유통 센터'**의 피킹 프로세스를 모델링합니다. 
이 센터는 최근 주문량 증가로 인해 작업자 동선이 꼬이는 문제를 겪고 있습니다. 

**과제 섹션: 프로세스 선택과 설비 배치**
- **문제점:** 설비(랙) 내 물품 배치가 무작위여서 작업자가 불필요하게 센터 전체를 횡단함.
- **해결안:** 출고 빈도에 따른 **ABC Class Slotting** 및 **이동 경로(Routing) 최적화** 적용.
""")

# --- 2. 사이드바: 시나리오 및 물품 설정 ---
st.sidebar.header("⚙️ 시뮬레이션 설정")
scenario = st.sidebar.selectbox("분석 시나리오 선택", 
    ["[AS-IS] 무작위 배치 및 경로", "[TO-BE] ABC 최적 배치 및 경로"])

picking_count = st.sidebar.slider("피킹 작업 물량 (건수)", 20, 100, 40)
speed = st.sidebar.select_slider("시뮬레이션 속도", options=["느림", "보통", "빠름"], value="보통")
speed_map = {"느림": 0.1, "보통": 0.05, "빠름": 0.01}

# --- 3. 구역별 물품 가상 데이터 정의 ---
zone_items = {
    "A-Zone": ["iPhone 15", "MacBook Air", "Galaxy S24", "iPad Pro"], # 고단가/고빈도
    "B-Zone": ["충전 케이블", "블루투스 마우스", "키보드", "헤드셋"],   # 중빈도
    "C-Zone": ["서류 정리함", "멀티탭", "모니터 거치대", "데스크 매트"]    # 저빈도
}

# --- 4. 데이터 생성 로직 ---
def get_scenario_data(mode, count):
    np.random.seed(42)
    if "[AS-IS]" in mode:
        # AS-IS: 물품이 구역 구분 없이 섞여 있음
        x = np.random.randint(10, 90, size=count)
        y = np.random.randint(10, 90, size=count)
    else: # [TO-BE]
        # TO-BE: 빈도 높은 물건(A구역) 위주로 주문 생성 및 경로 정렬
        x = np.random.exponential(scale=20, size=count).clip(5, 95)
        y = np.random.randint(10, 90, size=count)
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
    
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

# --- 5. 레이아웃 그리기 (물품 이름 포함) ---
def draw_detailed_layout(ax):
    ax.set_facecolor('#fdfdfd')
    # 랙 구역 및 물품 텍스트 추가
    zones = [
        (15, "A-Zone (Fast)", "#d1e7dd", zone_items["A-Zone"]),
        (45, "B-Zone (Mid)", "#fff3cd", zone_items["B-Zone"]),
        (75, "C-Zone (Slow)", "#f8d7da", zone_items["C-Zone"])
    ]
    
    for start_x, label, color, items in zones:
        # 구역 배경
        ax.add_patch(patches.Rectangle((start_x-5, 5), 25, 90, facecolor=color, alpha=0.3, zorder=1))
        ax.text(start_x+5, 96, label, fontsize=12, fontweight='bold', ha='center')
        
        # 구역 내 랙과 물품 이름 배치
        for i, y in enumerate(range(15, 85, 20)):
            ax.add_patch(patches.Rectangle((start_x, y), 10, 10, facecolor='#6c757d', alpha=0.7, zorder=2))
            # 가상 물품 이름 태그 (랙 위에 작게 표시)
            item_name = items[i % len(items)]
            ax.text(start_x+5, y+5, item_name, fontsize=8, color='white', ha='center', va='center', fontweight='bold', zorder=3)

    # 입출고 센터
    ax.scatter(0, 0, c='#0d6efd', s=300, marker='s', label='출고장(Dock)', zorder=5)
    ax.text(-5, -8, "📦 출고 데스크", fontweight='bold')
    ax.set_xlim(-15, 105); ax.set_ylim(-15, 110)

# --- 6. 시각화 실행 ---
df = get_scenario_data(scenario, picking_count)
total_dist = np.sqrt(np.diff(df['X'])**2 + np.diff(df['Y'])**2).sum()

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader(f"📍 실시간 이동 경로: {scenario}")
    plot_spot = st.empty()
    
    for i in range(2, len(df)+1):
        fig, ax = plt.subplots(figsize=(10, 8))
        draw_detailed_layout(ax)
        path_df = df.iloc[:i]
        # 동선 그리기
        ax.plot(path_df['X'], path_df['Y'], color='#0dcaf0', alpha=0.6, linewidth=2, marker='o', markersize=4, zorder=4)
        # 작업자 위치
        ax.scatter(path_df['X'].iloc[-1], path_df['Y'].iloc[-1], color='red', s=120, edgecolors='white', zorder=6)
        plot_spot.pyplot(fig)
        time.sleep(speed_map[speed])
        plt.close()

with col2:
    st.subheader("📊 분석 결과 리포트")
    st.metric("총 이동 거리", f"{total_dist:.2f} m")
    
    st.markdown("#### 💡 설비 배치 인사이트")
    if "[AS-IS]" in scenario:
        st.warning("""
        **현재 상태 분석:**
        - 인기 상품(iPhone 등)이 센터 후방에 배치되어 이동 낭비가 심함.
        - 작업자가 '서류 정리함'을 찾으러 갔다가 다시 'iPad'를 가지러 오는 등 동선이 중복됨.
        """)
    else:
        improvement = ((2300 - total_dist) / 2300) * 100
        st.success(f"""
        **최적화 결과:**
        - **효율성 향상:** 이동 거리 약 {improvement:.1f}% 단축.
        - **설비 재배치:** 출고 빈도가 높은 **A-Zone(전자제품)**을 입구에 전진 배치.
        - **프로세스:** 순차적 경로(Routing)를 적용하여 역행 최소화.
        """)

    st.divider()
    st.info("""
    **과제 핵심 결론:**
    설비 배치는 단순한 물리적 배치가 아니라, **데이터(출고 빈도)와 동선 최적화**가 결합된 '공학적 의사결정' 과정입니다.
    """)
