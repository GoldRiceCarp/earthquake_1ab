import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 페이지 설정
st.set_page_config(page_title="지구과학 지진 탐구", page_icon="🌋")

# 제목
st.title("🌋 골든타임을 확보하라: 지진파 분석")
st.write("아래 그래프를 분석하여 P파와 S파의 시작점을 찾고, 진원 거리를 계산하세요.")

# 사이드바 (입력창)
with st.sidebar:
    st.header("📝 분석관 정보")
    name = st.text_input("이름", "학생 이름")
    st.divider()
    st.write("설정")
    difficulty = st.radio("난이도", ["Level 1 (쉬움)", "Level 2 (어려움)"])

# 데이터 생성 함수
def get_data(diff):
    dist = 200 # 정답 거리
    vp, vs = 6.0, 3.5
    t = np.linspace(0, 80, 800)
    tp = dist/vp + 5
    ts = dist/vs + 5
    
    noise_amp = 0.3 if diff == "Level 1 (쉬움)" else 0.8
    np.random.seed(42)
    wave = np.random.normal(0, noise_amp, len(t))
    
    # P파, S파 추가
    if int(tp*10) < len(t): wave[int(tp*10):int(tp*10)+150] += np.sin(np.linspace(0, 10*np.pi, 150)) * 2
    if int(ts*10) < len(t): wave[int(ts*10):int(ts*10)+200] += np.sin(np.linspace(0, 10*np.pi, 200)) * 6
    return t, wave, tp, ts

# 데이터 로드
t_data, wave_data, true_p, true_s = get_data(difficulty)

# 메인 화면 구성
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("지진파 기록 (Seismogram)")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t_data, wave_data, 'k-', lw=0.8, alpha=0.7)
    
    # 학생 선택값
    p_pick = st.session_state.get('p', 10.0)
    s_pick = st.session_state.get('s', 20.0)
    
    ax.axvline(p_pick, c='blue', ls='--', label='P-Pick')
    ax.axvline(s_pick, c='red', ls='--', label='S-Pick')
    if s_pick > p_pick: ax.axvspan(p_pick, s_pick, color='yellow', alpha=0.2)
    ax.legend()
    st.pyplot(fig)

with col2:
    st.subheader("분석 도구")
    p_val = st.slider("P파 도착(초)", 0.0, 80.0, 10.0, 0.1, key='p')
    s_val = st.slider("S파 도착(초)", 0.0, 80.0, 20.0, 0.1, key='s')
    
    if st.button("결과 제출"):
        err = abs(p_val - true_p) + abs(s_val - true_s)
        st.divider()
        if err < 2.0:
            st.success("✅ 정답! 완벽합니다.")
            st.balloons()
            dist_calc = (s_val - p_val) * 8.4
            st.write(f"추정 거리: {dist_calc:.1f} km")
        else:
            st.error("❌ 오차가 큽니다. 다시 시도하세요!")
            if abs(p_val - true_p) > 1.0: st.caption("힌트: P파 시작점을 다시 보세요.")
