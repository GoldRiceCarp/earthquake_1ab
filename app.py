import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 페이지 설정
st.set_page_config(page_title="지구과학 지진 탐구", page_icon="🌋", layout="wide")

# 제목 및 설명
st.title("🌋 골든타임을 확보하라: 지진파 분석")
st.markdown("""
**[미션]** 제주 해역에서 지진이 감지되었습니다. 
노이즈가 섞인 지진 데이터를 분석하여 **P파와 S파의 도착 시각**을 정확히 찾아내고, 
**진원까지의 거리**를 계산하세요.
""")
st.divider()

# 사이드바 (입력창)
with st.sidebar:
    st.header("📝 분석관 정보")
    name = st.text_input("이름", "학생 이름")
    st.divider()
    st.write("🔧 설정")
    difficulty = st.radio("난이도 선택", ["Level 1 (기본)", "Level 2 (심화: 노이즈 심함)"])

# 데이터 생성 함수 (수정됨: 에러 방지 코드 추가)
def get_data(diff):
    dist = 200 # 정답 거리 (km)
    vp, vs = 6.0, 3.5
    
    # 시간축을 100초로 넉넉하게 늘림 (에러 방지 1)
    t = np.linspace(0, 100, 1000)
    
    tp = dist/vp + 5
    ts = dist/vs + 5
    
    # 난이도별 노이즈 설정
    noise_amp = 0.3 if diff == "Level 1 (기본)" else 0.8
    np.random.seed(42)
    wave = np.random.normal(0, noise_amp, len(t))
    
    # P파 만들기 (안전장치 추가)
    p_idx = int(tp * 10)
    p_len = 150
    if p_idx < len(t):
        # 그래프 끝을 벗어나지 않게 길이 조절
        actual_len = min(p_len, len(t) - p_idx)
        wave[p_idx : p_idx + actual_len] += np.sin(np.linspace(0, 10*np.pi, actual_len)) * 2
    
    # S파 만들기 (안전장치 추가)
    s_idx = int(ts * 10)
    s_len = 200
    if s_idx < len(t):
        actual_len = min(s_len, len(t) - s_idx)
        wave[s_idx : s_idx + actual_len] += np.sin(np.linspace(0, 10*np.pi, actual_len)) * 6
        
    return t, wave, tp, ts

# 데이터 로드
t_data, wave_data, true_p, true_s = get_data(difficulty)

# 메인 화면 구성
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("1️⃣ 지진파 기록 (Seismogram)")
    
    fig, ax = plt.subplots(figsize=(10, 4))
    # 그래프 그리기
    ax.plot(t_data, wave_data, 'k-', lw=0.8, alpha=0.7, label='Raw Data')
    
    # 학생이 선택한 값 표시 (초기값 설정)
    if 'p_pick' not in st.session_state: st.session_state['p_pick'] = 10.0
    if 's_pick' not in st.session_state: st.session_state['s_pick'] = 20.0
    
    p_val = st.session_state['p_pick']
    s_val = st.session_state['s_pick']
    
    ax.axvline(p_val, c='blue', ls='--', lw=2, label='Your P')
    ax.axvline(s_val, c='red', ls='--', lw=2, label='Your S')
    
    if s_val > p_val:
        ax.axvspan(p_val, s_val, color='yellow', alpha=0.2, label='PS Time')
        
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

with col2:
    st.subheader("2️⃣ 분석 도구")
    
    # 슬라이더 조작 시 session_state 업데이트
    p_input = st.slider("P파 도착(초)", 0.0, 100.0, 10.0, 0.1, key='p_slider')
    s_input = st.slider("S파 도착(초)", 0.0, 100.0, 20.0, 0.1, key='s_slider')
    
    # 슬라이더 값을 변수에 저장
    st.session_state['p_pick'] = p_input
    st.session_state['s_pick'] = s_input
    
    st.markdown("---")
    
    if st.button("🚀 결과 제출 (Check)"):
        err_p = abs(p_input - true_p)
        err_s = abs(s_input - true_s)
        total_err = err_p + err_s
        
        st.write(f"**측정된 PS시:** {s_input - p_input:.1f}초")
        
        if total_err < 2.0:
            st.success("✅ 정답입니다! 정확하게 분석하셨네요.")
            st.balloons()
            dist_calc = (s_input - p_input) * 8.4
            st.info(f"📍 추정 진원 거리: 약 {dist_calc:.1f} km")
        else:
            st.error("❌ 오차가 큽니다. 다시 시도해보세요.")
            if err_p > 1.0: st.caption("👉 힌트: P파는 미세하게 진동이 시작되는 곳입니다.")
            if err_s > 1.0: st.caption("👉 힌트: S파는 진폭이 갑자기 커지는 곳입니다.")
