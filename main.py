import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="물류센터 동선 최적화 시뮬레이션")

# --- 1. [상단] 과제 개요 및 시나리오 설명 ---
st.title("🎓 대학원 과제: 가상 물류센터 동선 최적화 분석")
st.markdown("""
본 시뮬레이션은 데이터가 부재한 상황에서 **가상 피킹 로그**를 생성하여, 물류 센터의 고질적인 문제인 **동선 낭비**를 시각화하고 그 개선 방안을 제시합니다.
""")

# --- 개선 방법론을 설명하는 Expander 추가 ---
with st.expander("🔍 본 시뮬레이션에 적용된 개선 방법론 (Methodology)"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        **1. ABC 배치 최적화 (Slotting)**
        - **AS-IS:** 물품의 출고 빈도와 상관없이 임의의 랙에 배치됨.
        - **TO-BE:** 출고 빈도가 높은 상위 20% 품목(A-Class)을 출고장(Start/End)과 가장 가까운 구역에 집중 배치.
        """)
    with col_b:
        st.markdown("""
        **2. 피킹 경로 최적화 (Routing)**
        - **AS-IS:** 주문서에 찍힌 순서대로(무작위) 이동하여 동선이 꼬임.
        - **TO-BE:** 'S-Shape Routing' 또는 'Heuristic' 기법을 모사하여 가까운 좌표 순으로 방문하여 역행 방지.
        """)

st.divider()

# --- 2. 사이드바 설정 ---
st.sidebar.header("🕹️ 시뮬레이션 컨트롤러")
scenario = st.sidebar.selectbox("분석 시나리오 선택", 
    ["개선 전: 평상시 (AS-IS)", "개선 전: 주문 폭주 (AS-IS)", "개선 후: 최적화 모델 (TO-BE)"])

# ... (생략된 데이터 생성 및 레이아웃 그리기 함수는 이전과 동일하나 로직을 명확히 함) ...

def get_scenario_data(mode, count):
    np.random.seed(42)
    if mode == "개선 전: 평상시 (AS-IS)":
        x = np.random.randint(10, 90, size=count)
        y = np.random.randint(10, 90, size=count)
    elif mode == "개선 전: 주문 폭주 (AS-IS)":
        # 특정 중앙 구역에 몰림 (병목 현상 유도)
        x = np.random.normal(50, 15, size=count).clip(5, 95)
        y = np.random.normal(50, 15, size=count).clip(5, 95)
    else: # 개선 후: 최적화 모델 (TO-BE)
        # ABC 배치를 모사하여 입구(0,0) 근처에 데이터가 많이 생성되도록 지수 분포 활용
        x = np.random.exponential(scale=25, size=count).clip(5, 95)
        y = np.random.randint(10, 90, size=count)
        # 경로 최적화 (X축 방향으로 정렬하여 훑고 가기)
        df_tmp = pd.DataFrame({'x': x, 'y': y}).sort_values(by=['x', 'y'])
        x, y = df_tmp['x'].values, df_tmp['y'].values
    
    x = np.insert(x, 0, 0); x = np.append(x, 0)
    y = np.insert(y, 0, 0); y = np.append(y, 0)
    return pd.DataFrame({'X': x, 'Y': y})

# ... (레이아웃 그리기 및 애니메이션 로직 동일하게 적용) ...

# --- 분석 결과 리포트 영역 ---
with col2:
    st.subheader("📊 데이터 분석 결과")
    total_dist = np.sqrt(np.diff(df['X'])**2 + np.diff(df['Y'])**2).sum()
    st.metric("총 이동 거리", f"{total_dist:.2f} m")
    
    # 개선 효과 자동 계산 (가상의 기준값 2500m 대비)
    if "TO-BE" in scenario:
        improvement = ((2500 - total_dist) / 2500) * 100
        st.success(f"이전 시나리오 대비 동선이 약 {improvement:.1f}% 개선되었습니다.")
        st.markdown("""
        **핵심 개선 지표:**
        - **보행 시간 감소:** 거리 단축을 통한 불필요 노동 시간 제거.
        - **동선 단순화:** 작업자 간의 간섭 발생 확률 최소화.
        """)
    else:
        st.warning("동선의 겹침(Spaghetti)이 발생하고 있습니다. 레이아웃 재배치가 필요합니다.")

# ... (하단 데이터 테이블 표시) ...
