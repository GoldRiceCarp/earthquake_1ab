import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import random

# -----------------------------------------------------------------------------
# 1. 초기 설정 및 세션 관리
# -----------------------------------------------------------------------------
st.set_page_config(page_title="지구과학 심화 탐구", page_icon="🌋", layout="wide")

# 문제 은행 (Group A를 위한 심화 문제)
if 'quiz_bank' not in st.session_state:
    st.session_state['quiz_bank'] = [
        {"q": "Q. 진원 거리가 1000km 이상일 때, P파와 S파 사이에 도착하는 표면파(L파)의 특징으로 옳은 것은?", 
         "options": ["진폭이 가장 작다.", "전파 속도가 가장 빠르다.", "지구 중심을 통과한다.", "진폭이 가장 크고 피해가 크다."], 
         "a": "진폭이 가장 크고 피해가 크다."},
        {"q": "Q. 동일한 지진에 대해 관측소 A가 관측소 B보다 진원 거리가 멀다. A에서 관측되는 특징은?", 
         "options": ["PS시가 더 짧다.", "진폭이 더 크다.", "PS시가 더 길다.", "P파 도착 시각이 더 빠르다."], 
         "a": "PS시가 더 길다."},
        {"q": "Q. P파의 속도가 8km/s, S파의 속도가 4km/s일 때, PS시가 10초라면 진원 거리는?", 
         "options": ["40km", "60km", "80km", "100km"], 
         "a": "80km"}, # d = (8*4)/(8-4) * 10 = 80
        {"q": "Q. 지구 내부의 외핵을 S파가 통과하지 못하는 이유는?", 
         "options": ["외핵이 고체라서", "외핵이 액체라서", "밀도가 너무 낮아서", "온도가 너무 높아서"], 
         "a": "외핵이 액체라서"}
    ]

# 현재 풀고 있는 보너스 문제 저장
if 'current_quiz' not in st.session_state:
    st.session_state['current_quiz'] = None

# 교사 피드백 저장
if 'teacher_feedback' not in st.session_state:
    st.session_state['teacher_feedback'] = ""

# -----------------------------------------------------------------------------
# 2. 데이터 생성 함수 (난이도 상향: 노이즈 강화 & P파 진폭 축소)
# -----------------------------------------------------------------------------
def get_seismic_data(difficulty):
    dist = np.random.randint(150, 400) # 랜덤 거리 (매번 달라짐)
    vp, vs = 6.0, 3.5 # 속도 모델
    
    t = np.linspace(0, 100, 1000)
    tp = dist/vp + 5
    ts = dist/vs + 5
    
    # 난이도 조절
    if difficulty == "High (심화)":
        noise_amp = 0.5  # 노이즈 심함
        p_amp = 1.5      # P파 잘 안 보임
    else:
        noise_amp = 0.2
        p_amp = 3.0
        
    np.random.seed(42) # 노이즈 패턴 고정 (새로고침해도 그래프 모양 유지 위해)
    wave = np.random.normal(0, noise_amp, len(t))
    
    # 파동 합성
    p_idx = int(tp * 10)
    if p_idx < len(t):
        length = min(150, len(t)-p_idx)
        wave[p_idx:p_idx+length] += np.sin(np.linspace(0, 10*np.pi, length)) * p_amp
        
    s_idx = int(ts * 10)
    if s_idx < len(t):
        length = min(200, len(t)-s_idx)
        wave[s_idx:s_idx+length] += np.sin(np.linspace(0, 10*np.pi, length)) * (p_amp * 2.5)
        
    return t, wave, tp, ts, dist

# -----------------------------------------------------------------------------
# 3. 사이드바 (설정 & 교사 피드백 모드)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    diff_mode = st.radio("난이도", ["Normal (기본)", "High (심화)"])
    st.info("High 모드: P파가 작고 노이즈가 심합니다.")
    
    st.divider()
    
    # [3] 교사 직접 피드백 기능
    with st.expander("👨‍🏫 선생님 전용 (Teacher Only)"):
        pw = st.text_input("비밀번호", type="password")
        if pw == "1234": # 선생님 비밀번호 (변경 가능)
            st.success("인증되었습니다.")
            fb = st.text_area("학생에게 보낼 피드백 입력:", st.session_state['teacher_feedback'])
            if st.button("피드백 전송"):
                st.session_state['teacher_feedback'] = fb
                st.success("전송 완료! 학생 화면에 표시됩니다.")
        elif pw:
            st.error("비밀번호가 틀렸습니다.")

# -----------------------------------------------------------------------------
# 4. 메인 화면
# -----------------------------------------------------------------------------
st.title("🌋 지진파 정밀 분석 & 진원 거리 추론")

# 교사 피드백 표시 영역
if st.session_state['teacher_feedback']:
    st.warning(f"👨‍🏫 **선생님 피드백:** {st.session_state['teacher_feedback']}")

t_data, wave_data, true_p, true_s, true_dist = get_seismic_data(diff_mode)

# 그래프 영역
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(t_data, wave_data, 'k-', lw=0.8, alpha=0.7, label='Seismogram')

# 학생 인터랙션
if 'p_slider' not in st.session_state: st.session_state['p_slider'] = 10.0
if 's_slider' not in st.session_state: st.session_state['s_slider'] = 20.0

p_val = st.session_state['p_slider']
s_val = st.session_state['s_slider']

ax.axvline(p_val, c='blue', ls='--', label='Your P')
ax.axvline(s_val, c='red', ls='--', label='Your S')
if s_val > p_val:
    ax.axvspan(p_val, s_val, color='yellow', alpha=0.2)
ax.legend()
st.pyplot(fig)

# -----------------------------------------------------------------------------
# 5. 문제 풀이 영역 (난이도 상향: 직접 계산)
# -----------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 파형 분석")
    p_in = st.slider("P파 도착(초)", 0.0, 100.0, 10.0, 0.1, key='p_slider')
    s_in = st.slider("S파 도착(초)", 0.0, 100.0, 20.0, 0.1, key='s_slider')

with col2:
    st.subheader("2. 진원 거리 계산")
    st.markdown("""
    * **공식 힌트:** $D \approx 8.4 \times (T_s - T_p)$
    * PS시를 이용하여 진원까지의 거리를 직접 계산하세요.
    """)
    user_dist = st.number_input("계산한 진원 거리 (km)", min_value=0.0, step=1.0)
    submit = st.button("🚀 최종 제출")

# -----------------------------------------------------------------------------
# 6. 결과 처리 및 그룹 분화 (A/B)
# -----------------------------------------------------------------------------
if submit:
    # 오차 계산
    time_err = abs(p_in - true_p) + abs(s_in - true_s)
    dist_err = abs(user_dist - true_dist)
    
    st.divider()
    
    # [그룹 A] 정답 (시간 오차 2초 이내 & 거리 오차 30km 이내)
    if time_err < 2.0 and dist_err < 30.0:
        st.success(f"🏆 **[Group A: 전문가]** 완벽합니다! (정답 거리: {true_dist}km)")
        st.balloons()
        
        # 추가 피드백 (심화 문제 출제)
        st.markdown("### 🎁 보너스 미션: 심화 문제 도전")
        st.info("뛰어난 분석력입니다! 당신의 실력을 증명할 마지막 문제가 주어집니다.")
        
        if st.session_state['current_quiz'] is None:
            st.session_state['current_quiz'] = random.choice(st.session_state['quiz_bank'])
            
        quiz = st.session_state['current_quiz']
        st.write(f"**{quiz['q']}**")
        choice = st.radio("정답 선택:", quiz['options'], key="quiz_radio")
        
        if choice == quiz['a']:
            st.write("✅ **정답입니다!** 완벽하게 단원을 마스터하셨군요.")
        else:
            st.write("❌ 다시 생각해보세요.")

    # [그룹 B] 오답 (재시도 유도)
    else:
        st.error(f"⚠️ **[Group B: 재분석 필요]** 오차가 발생했습니다.")
        
        # 맞춤형 피드백 제공
        if time_err >= 2.0:
            st.write("🔍 **파형 분석 힌트:**")
            if abs(p_in - true_p) > 1.0:
                st.caption(f"- P파는 노이즈보다 아주 조금 더 크게 튀는 시점입니다. (현재 {p_in}초 선택함)")
            if abs(s_in - true_s) > 1.0:
                st.caption(f"- S파는 진동이 급격히 커지는 두 번째 구간입니다. (현재 {s_in}초 선택함)")
        
        if dist_err >= 30.0:
            ps_time = s_in - p_in
            st.write("🧮 **계산 힌트:**")
            st.caption(f"- 당신이 찾은 PS시는 {ps_time:.1f}초입니다.")
            st.caption(f"- 공식 $8.4 \\times {ps_time:.1f}$ 을 다시 계산해보세요.")
        
        st.warning("🔄 **포기하지 마세요!** 힌트를 참고하여 값을 수정하고 다시 제출 버튼을 누르세요.")
