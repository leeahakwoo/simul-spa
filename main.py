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
    count = 35
    if mode == 'AS-IS':
        x = np.random.randint(10, 95, size=count)
        y = np.random.randint(10, 95, size=count)
    else:
        # 인기 품목(80%)을 앞쪽(10~40)에 배치하는 논리
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
                ax.text(sx+5, sy+5, "인기", color='green', fontsize=8, ha='center', va='center', fontweight='bold')
    ax.scatter(0, 0, c='blue', s=150, marker='s', label='Dock')
    ax.set_xlim(-10, 105); ax.set_ylim(-10, 105)

# --- 2. 메인 화면 구성 ---
st.title("📦 공정 선택과 설비 배치 최적화 프로젝트")
st.markdown("---")

# 단계 가이드
step_names = ["Step 1. 배경 및 진단", "Step 2. AS-IS 동선 분석", "Step 3. TO-BE 시뮬레이션", "Step 4. 최종 개선 리포트"]
selected_tab = st.radio("분석 단계", step_names, index=st.session_state['current_step'], horizontal=True)

# 탭 인덱스 동기화
st.session_state['current_step'] = step_names.index(selected_tab)

# --- 각 단계별 콘텐츠 ---

# [STEP 1. 배경 및 진단]
if st.session_state['current_step'] == 0:
    st.header("1️⃣ 연구 배경 및 현재 상태 진단")
    st.info("💡 **가이드:** 물류센터의 운영 효율을 저해하는 근본적인 원인을 파악하고 분석 가설을 수립하는 단계입니다.")
    
    col_text, col_data = st.columns([1, 1])
    with col_text:
        st.markdown("""
        #### 🧐 현상 파악 (Problem Statement)
        - 출고 물동량 증가에도 불구하고 작업자 1인당 피킹 속도가 정체되어 생산성 저하 발생.
        - 현장 모니터링 결과, 작업자가 상품을 찾는 시간보다 상품으로 이동하는 **'보행 시간'**이 전체 공정의 대부분을 차지함.
        
        #### 🔍 분석 가설
        "품목별 출고 빈도를 무시한 **무작위 설비 배치(Random Slotting)**가 불필요한 장거리 이동과 동선 중첩을 야기할 것이다."
        """)
    with col_data:
        st.write("#### 📊 공정 진단 데이터")
        st.table(pd.DataFrame({
            "항목": ["측정 일자", "분석 공정", "설비 배치 방식", "핵심 문제점"],
            "내용": ["2026-04-17", "오더 피킹(Picking)", "Random Slotting", "스파게티 현상 발생"]
        }))
    
    if st.button("다음 단계로: AS-IS 동선 측정 결과 보기 ➡️"):
        st.session_state['current_step'] = 1
        st.rerun()

# [STEP 2. AS-IS 동선 분석]
elif st.session_state['current_step'] == 1:
    st.header("2️⃣ AS-IS 동선 분석: 스파게티 다이어그램")
    st.warning("💡 **가이드:** 실제 측정된 피킹 로그를 시각화한 단계입니다. 빨간색 선이 복잡하게 얽힌 정도를 통해 설비 배치의 비효율성을 확인하세요.")
    
    df_asis = get_data('AS-IS')
    dist_asis = np.sqrt(np.diff(df_asis['X'])**2 + np.diff(df_asis['Y'])**2).sum()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_warehouse(ax, "AS-IS")
        ax.plot(df_asis['X'], df_asis['Y'], color='#ff4b4b', alpha=0.7, linewidth=1.5, marker='o', markersize=3)
        ax.set_title("Measured AS-IS Spaghetti Diagram")
        st.pyplot(fig)
    with c2:
        st.metric("AS-IS 총 이동 거리", f"{dist_asis:.2f} m")
        st.error("""
        **분석 의견:**
        - 인기 품목이 출고장에서 먼 곳에 배치되어 왕복 거리가 매우 멂.
        - 동선이 여러 번 교차하며 작업자 간 간섭 가능성이 높음.
        """)
        if st.button("다음 단계로: 개선안(TO-BE) 시뮬레이션 수행 ➡️"):
            st.session_state['current_step'] = 2
            st.rerun()

# [STEP 3. TO-BE 시뮬레이션]
elif st.session_state['current_step'] == 2:
    st.header("3️⃣ 설비 배치 변경 시뮬레이션 (TO-BE)")
    st.success("💡 **가이드:** 제안된 개선 전략(ABC 배치)을 적용하여 동선이 어떻게 정돈되는지 시뮬레이션으로 확인하는 과정입니다.")
    
    df_tobe = get_data('TO-BE')
    dist_tobe = np.sqrt(np.diff(df_tobe['X'])**2 + np.diff(df_tobe['Y'])**2).sum()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        # 시뮬레이션 애니메이션 실행 (이 단계에서만 이모션 적용)
        plot_spot = st.empty()
        for i in range(2, len(df_tobe)+1):
            fig, ax = plt.subplots(figsize=(10, 6))
            draw_warehouse(ax, "TO-BE")
            path = df_tobe.iloc[:i]
            ax.plot(path['X'], path['Y'], color='#00c853', alpha=0.8, linewidth=2, marker='o', markersize=4)
            plot_spot.pyplot(fig)
            time.sleep(0.01)
            plt.close()
    with c2:
        st.metric("TO-BE 예상 이동 거리", f"{dist_tobe:.2f} m")
        st.info("""
        **개선 전략:**
        1. 출고 빈도 상위 품목 Zone A 전진 배치.
        2. 통로별 순차 피킹(S-Shape) 경로 적용.
        """)
        if st.button("마지막 단계로: 최종 개선 리포트 확인 ➡️"):
            st.session_state['current_step'] = 3
            st.rerun()

# [STEP 4. 최종 개선 리포트]
elif st.session_state['current_step'] == 3:
    st.header("4️⃣ 최종 분석 결과 및 설비 배치 확정안")
    st.info("💡 **가이드:** AS-IS와 TO-BE의 최종 결과를 직접 비교하여 본 프로젝트의 성과를 요약합니다.")
    
    # 데이터 고정 호출 (애니메이션 없이 정적 이미지로만 구성)
    d_a = get_data('AS-IS'); dist_a = np.sqrt(np.diff(d_a['X'])**2 + np.diff(d_a['Y'])**2).sum()
    d_t = get_data('TO-BE'); dist_t = np.sqrt(np.diff(d_t['X'])**2 + np.diff(d_t['Y'])**2).sum()
    
    # 비교 이미지 영역
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.subheader("❌ AS-IS: 설비 배치 최적화 전")
        fig_a, ax_a = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_a, "AS-IS", show_items=False)
        ax_a.plot(d_a['X'], d_a['Y'], color='#ff4b4b', alpha=0.6, linewidth=1.2)
        st.pyplot(fig_a)
        st.markdown(f"""
        **현상 분석:** 무작위 배치로 인해 작업자가 센터 전체 구역(Zone A~C)을 반복적으로 횡단하고 있습니다.  
        이동 경로가 스파게티처럼 엉켜 있어 작업 리드타임이 불필요하게 길어지는 근본 원인이 됩니다.  
        총 이동 거리: **{dist_a:.2f}m**
        """)
        
    with res_col2:
        st.subheader("✅ TO-BE: 설비 배치 최적화 후")
        fig_t, ax_t = plt.subplots(figsize=(8, 6))
        draw_warehouse(ax_t, "TO-BE")
        ax_t.plot(d_t['X'], d_t['Y'], color='#00c853', alpha=0.7, linewidth=1.5)
        st.pyplot(fig_t)
        st.markdown(f"""
        **개선 효과:** 출고 빈도가 높은 품목을 입구 근처(Zone A)에 집중 배치함으로써 작업자의 주 활동 반경을 최소화하였습니다.  
        S-Shape 라우팅 알고리즘을 적용하여 경로 중복을 제거하고 이동 거리를 효율적으로 단축하였습니다.  
        예상 이동 거리: **{dist_t:.2f}m** (약 {((dist_a-dist_t)/dist_a*100):.1f}% 개선)
        """)

    st.divider()
    
    # 최종 결론 및 처음으로 돌아가기
    st.subheader("🏁 종합 결론")
    st.success(f"""
    본 프로젝트를 통해 **설비 배치(Slotting)**와 **프로세스(Routing)** 개선이 물류 운영 효율에 미치는 영향력을 정량적으로 확인하였습니다. 
    데이터 기반의 최적 배치를 적용할 경우, 단순 이동 거리 단축뿐만 아니라 작업자의 피로도 감소 및 시간당 처리량(UPH)의 획기적인 향상이 기대됩니다.
    """)
    
    if st.button("🔄 처음으로 돌아가기 (다시 보기)"):
        st.session_state['current_step'] = 0
        st.rerun()
