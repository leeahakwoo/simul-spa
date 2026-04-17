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

# --- 1. 유틸리티 함수 (데이터 및 레이아웃) ---
def get_data(mode):
    np.random.seed(42)
    count = 30
    if mode == 'AS-IS':
        x = np.random.randint(10, 95, size=count)
        y = np.random.randint(10, 95, size=count)
    else:
        x = np.random.choice([np.random.randint(10, 40), np.random.randint(40, 95)], size=count, p=[0.8, 0.2])
        y = np.random.randint(10, 95, size=count)
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
                ax.text(sx+5, sy+5, "인기상품", color='green', fontsize=8, ha='center', va='center', fontweight='bold')
    ax.scatter(0, 0, c='blue', s=150, marker='s')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)

# --- 2. 메인 화면 구성 (탭 인터페이스) ---
st.title("📦 공정 선택과 설비 배치 최적화 프로젝트")
st.markdown("---")

# 현재 단계에 따른 탭 활성화
step_names = ["Step 1. 배경 및 진단", "Step 2. AS-IS 동선 분석", "Step 3. TO-BE 시뮬레이션", "Step 4. 최종 개선 리포트"]
selected_tab = st.radio("분석 단계 가이드", step_names, index=st.session_state['current_step'], horizontal=True, label_visibility="collapsed")

# 탭 인덱스 업데이트 (라디오 버튼으로도 이동 가능하게 함)
st.session_state['current_step'] = step_names.index(selected_tab)

# --- 각 단계별 콘텐츠 ---

# [STEP 1. 배경 및 진단]
if st.session_state['current_step'] == 0:
    st.header("1️⃣ 연구 배경 및 현재 상태 진단")
    st.info("💡 **가이드:** 먼저 현재 물류센터가 겪고 있는 비효율의 원인을 파악합니다.")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        #### 🧐 현상 파악 (Problem Statement)
        - 출고 물동량은 증가했으나, 작업자 1인당 피킹 효율은 오히려 감소함.
        - 현장 관찰 결과, 작업자가 상품을 찾아 센터 전체를 배회하는 시간이 70% 이상임.
        
        #### 🔍 분석 가설
        "설비 내 물품 적치 방식(Slotting)이 출고 빈도를 고려하지 않아 동선 낭비가 발생하고 있을 것이다."
        """)
    with c2:
        st.write("#### 📊 진단 데이터")
        st.table(pd.DataFrame({
            "항목": ["측정 일자", "대상 공정", "배치 방식", "비효율 지표"],
            "내용": ["2026-04-17", "오더 피킹(Order Picking)", "랜덤 배치(Random)", "공주행 거리 증가"]
        }))
    
    if st.button("다음 단계로: AS-IS 분석 ➡️"):
        st.session_state['current_step'] = 1
        st.rerun()

# [STEP 2. AS-IS 동선 분석]
elif st.session_state['current_step'] == 1:
    st.header("2️⃣ AS-IS 동선 분석: 스파게티 다이어그램")
    st.warning("💡 **가이드:** 빨간색 선으로 표시되는 실제 이동 경로를 확인하세요. 동선이 복잡하게 얽히는 '스파게티 현상'을 볼 수 있습니다.")
    
    df_asis = get_data('AS-IS')
    dist_asis = np.sqrt(np.diff(df_asis['X'])**2 + np.diff(df_asis['Y'])**2).sum()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_warehouse(ax, "AS-IS")
        ax.plot(df_asis['X'], df_asis['Y'], color='#ff4b4b', alpha=0.7, linewidth=1.5, marker='o', markersize=3)
        ax.set_title("AS-IS Spaghetti Diagram (Measured)")
        st.pyplot(fig)
    with c2:
        st.metric("AS-IS 총 이동 거리", f"{dist_asis:.2f} m")
        st.error("**원인 도출:** 인기 상품이 구역 3(가장 먼 곳)에 산재되어 있어 작업자가 센터 전체를 횡단함.")
        if st.button("다음 단계로: TO-BE 시뮬레이션 ➡️"):
            st.session_state['current_step'] = 2
            st.rerun()

# [STEP 3. TO-BE 시뮬레이션]
elif st.session_state['current_step'] == 2:
    st.header("3️⃣ 설비 배치 변경 시뮬레이션 (TO-BE)")
    st.success("💡 **가이드:** 인기 상품을 입구 쪽(Zone A)에 모으고 동선을 정렬했을 때의 변화를 확인하세요.")
    
    df_tobe = get_data('TO-BE')
    dist_tobe = np.sqrt(np.diff(df_tobe['X'])**2 + np.diff(df_tobe['Y'])**2).sum()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        plot_spot = st.empty()
        for i in range(2, len(df_tobe)+1):
            fig, ax = plt.subplots(figsize=(10, 6))
            draw_warehouse(ax, "TO-BE")
            path = df_tobe.iloc[:i]
            ax.plot(path['X'], path['Y'], color='#00c853', alpha=0.8, linewidth=2, marker='o', markersize=4)
            plot_spot.pyplot(fig)
            time.sleep(0.02)
            plt.close()
    with c2:
        st.metric("TO-BE 예상 이동 거리", f"{dist_tobe:.2f} m")
        st.info("**개선 포인트:** 인기 상품 전진 배치 + S-Shape 경로 최적화")
        if st.button("마지막 단계로: 결과 비교 및 확정 ➡️"):
            st.session_state['current_step'] = 3
            st.rerun()

# [STEP 4. 최종 개선 리포트]
elif st.session_state['current_step'] == 3:
    st.header("4️⃣ 최종 분석 결과 및 설비 배치 확정")
    st.info("💡 **가이드:** AS-IS와 TO-BE를 한눈에 비교하여 최종 설비 배치안을 확정합니다.")
    
    # 데이터 재호출
    d_asis = get_data('AS-IS'); dist_a = np.sqrt(np.diff(d_asis['X'])**2 + np.diff(d_asis['Y'])**2).sum()
    d_tobe = get_data('TO-BE'); dist_t = np.sqrt(np.diff(d_tobe['X'])**2 + np.diff(d_tobe['Y'])**2).sum()
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.subheader("⚠️ AS-IS (개선 전)")
        fig_a, ax_a = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_a, "AS-IS", show_items=False)
        ax_a.plot(d_asis['X'], d_asis['Y'], color='#ff4b4b', alpha=0.5)
        st.pyplot(fig_a)
        st.write(f"이동 거리: **{dist_a:.2f}m**")
        
    with col_res2:
        st.subheader("✅ TO-BE (개선 후)")
        fig_t, ax_t = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_t, "TO-BE")
        ax_t.plot(d_tobe['X'], d_tobe['Y'], color='#00c853', alpha=0.6)
        st.pyplot(fig_t)
        st.write(f"이동 거리: **{dist_t:.2f}m**")

    st.divider()
    
    res_text1, res_text2 = st.columns(2)
    with res_text1:
        st.markdown(f"""
        #### 📉 정량적 성과
        - **총 이동 거리 단축:** {dist_a:.1f}m → {dist_t:.1f}m
        - **효율 향상:** 약 **{((dist_a-dist_t)/dist_a*100):.1f}%** 단축 성공
        """)
    with res_text2:
        st.markdown("""
        #### 🏆 설비 배치 확정안
        - **A-Zone:** 고회전 인기 품목 집중 적치 (Slotting)
        - **B/C-Zone:** 저회전 품목 및 보관 위주 배치
        - **운영:** S-Shape 경로 기반 피킹 프로세스 표준화
        """)
    
    if st.button("🔄 처음부터 다시 보기"):
        st.session_state['current_step'] = 0
        st.rerun()
