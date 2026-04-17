import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 물류센터 동선 최적화 분석 (Spaghetti Diagram)")

# 데이터 로드 (위에서 생성한 가상 CSV 사용)
df_asis = pd.read_csv('warehouse_data_asis.csv')
df_tobe = pd.read_csv('warehouse_data_tobe.csv')

# 이동 거리 계산 함수
def calculate_distance(df):
    dist = np.sqrt(np.diff(df['X'])**2 + np.diff(df['y'])**2).sum()
    return dist

dist_asis = calculate_distance(df_asis)
dist_tobe = calculate_distance(df_tobe)

# 메트릭 표시
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("AS-IS 총 이동거리", f"{dist_asis:.1f}m")
col_m2.metric("TO-BE 총 이동거리", f"{dist_tobe:.1f}m", delta=f"-{((dist_asis-dist_tobe)/dist_asis*100):.1f}%")
col_m3.info("개선 포인트: ABC 분석 기반 구역(Zone)별 순차 피킹 적용")

# 시각화 레이아웃
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚠️ 개선 전: 무작위 피킹 동선")
    fig, ax = plt.subplots(figsize=(8, 8))
    # 레이아웃(랙) 배경 그리기
    ax.set_facecolor('#f0f0f0')
    ax.plot(df_asis['X'], df_asis['y'], color='red', alpha=0.5, linewidth=1.5, label='Path')
    ax.scatter(df_asis['X'], df_asis['y'], c='black', s=20, zorder=3)
    ax.scatter(0, 0, c='green', s=100, marker='s', label='Start/End') # 출입구
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105)
    ax.legend()
    st.pyplot(fig)
    st.write("설명: 피킹 리스트 순서대로 이동하여 동선이 꼬이고 중복 이동이 많음.")

with col2:
    st.subheader("✅ 개선 후: 경로 최적화 동선")
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor('#f0f0f0')
    # 구역별로 정렬된 데이터 시각화
    ax.plot(df_tobe['X'], df_tobe['y'], color='blue', alpha=0.6, linewidth=2, label='Optimized Path')
    ax.scatter(df_tobe['X'], df_tobe['y'], c='black', s=20, zorder=3)
    ax.scatter(0, 0, c='green', s=100, marker='s', label='Start/End')
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105)
    ax.legend()
    st.pyplot(fig)
    st.write("설명: Zone별/위치별 정렬 피킹을 통해 '되돌아가는 동선'을 최소화함.")

st.divider()
st.subheader("📋 가상 피킹 로그 데이터 (Raw Data)")
st.dataframe(df_asis.head(10))
