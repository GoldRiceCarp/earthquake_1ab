import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import random
import time
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 초기 설정 및 문제 은행 (Earth Science I Quiz Bank)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="지진파 정밀 분석 센터", page_icon="🌋", layout="wide")

# 문제 은행 (10문제 이상)
QUIZ_BANK = [
    {"q": "지진의 '규모(Magnitude)'에 대한 설명으로 옳은 것은?", "options": ["관측소마다 다르게 측정된다.", "지진 발생 시 방출된 에너지의 총량이다.", "진원 거리가 멀수록 작아진다.", "진도(Intensity)와 같은 개념이다."], "a": "지진 발생 시 방출된 에너지의 총량이다."},
    {"q": "P파와 S파의 성질에 대한 설명으로 옳은 것은?", "options": ["P파는 고체만 통과한다.", "S파는 액체를 통과할 수 있다.", "P파의 전파 속도가 S파보다 빠르다.", "S파는 종파(Longitudinal wave)이다."], "a": "P파의 전파 속도가 S파보다 빠르다."},
    {"q": "동일한 지진 관측소에서 PS시가 길다는 것은 무엇을 의미하는가?", "options": ["지진의 규모가 크다.", "진원 깊이가 얕다.", "진원까지의 거리가 멀다.", "지반이 단단하다."], "a": "진원까지의 거리가 멀다."},
    {"q": "지구 내부 구조 중 S파가 통과하지 못해 '암영대'를 만드는 층은?", "options": ["맨틀", "외핵", "내핵", "지각"], "a": "외핵"},
    {"q": "세 곳 이상의 관측소에서 진원 거리를 알 때, 진앙을 찾는 방법은?", "options": ["세 원의 교점을 찾는다.", "진폭이 가장 큰 곳을 찾는다.", "PS시가 가장 짧은 곳을 찾는다.", "세 관측소의 중점을 연결한다."], "a": "세 원의 교점을 찾는다."},
    {"q": "해양판과 대륙판이 충돌하는 수렴형 경계에서 주로 발생하는 지진은?", "options": ["천발 지진만 발생한다.", "심발 지진은 발생하지 않는다.", "베니오프대를 따라 천발~심발 지진이 모두 발생한다.", "지진이 거의 발생하지 않는다."], "a": "베니오프대를 따라 천발~심발 지진이 모두 발생한다."},
    {"q": "지진 해일(Tsunami)의 전파 속도에 가장 큰 영향을 미치는 요인은?", "options": ["바람의 세기", "해수면의 온도", "바다의 수심", "달의 인력"], "a": "바다의 수심"},
    {"q": "지진파의 속도가 주변보다 느린 곳(저속도층)은 일반적으로 어떤 상태인가?", "options": ["온도가 높고 밀도가 낮다(부분 용융).", "온도가 낮고 단단하다.", "맨틀 대류의 하강부이다.", "지각의 두께가 얇다."], "a": "온도가 높고 밀도가 낮다(부분 용융)."},
    {"q": "리히터 규모가 1 증가할 때, 지진 에너지는 약 몇 배 증가하는가?", "options": ["10배", "32배", "100배", "1000배"], "a": "32배"},
    {"q": "다음 중 판의 발산형 경계(해령)에서 주로 관측되는 특징은?", "options": ["습곡 산맥 형성", "심발 지진 활발", "새로운 지각 생성 및 천발 지진", "화산 활동 없음"], "a": "새로운 지각 생성 및 천발 지진"}
]

# 세션 상태 초기화
if 'stage' not in st.session_state: st.session_state['stage'] = 'analysis' # analysis, quiz
if 'quiz_index' not in st.session_state: st.session_state['quiz_index'] = -1
if 'current_quiz' not in st.session_state: st.session_state['current_quiz'] = None
if 'quiz_solved' not in st.session_state: st.session_state['quiz_solved'] = False # 정답 맞춤 여부
if 'feedback_msg' not in st.session_state: st.session_state['feedback_msg'] = ""

# -----------------------------------------------------------------------------
# 2. 데이터 생성 (Hard Mode Fixed)
# -----------------------------------------------------------------------------
def get_hard_data():
    dist = np.random.randint(200, 500) # 200~500km 랜덤
    vp, vs = 6.0, 3.5
    
    t = np.linspace(0, 100, 1000)
    tp = dist/vp + 5
    ts = dist/vs + 5
    
    # Hard Mode 설정 (노이즈 심함, P파 작음)
    noise_amp = 0.6
    p_amp = 1.8
    
    np.random.seed(int(time.time())) # 매번 다르게
    wave = np.random.normal(0, noise_amp, len(t))
    
    # P파
    p_idx = int(tp * 10)
    if p_idx < len(t):
        length = min(150, len(t)-p_idx)
        wave[p_idx:p_idx+length] += np.sin(np.linspace(0, 10*np.pi, length)) * p_amp
    
    # S파
    s_idx = int(ts * 10)
    if s_idx < len(t):
        length = min(200, len(t)-s_idx)
        wave[s_idx:s_idx+length] += np.sin(np.linspace(0, 10*np.pi, length)) * (p_amp * 3.0)
        
    return t, wave, tp, ts, dist

# 데이터 로드 (버튼 누르면 새로고침 효과)
if 'wave_data' not in st.session_state:
    t, w, tp, ts, d = get_hard_data()
    st.session_state['wave_data'] = (t, w, tp, ts, d)

t_data, wave_data, true_p, true_s, true_dist = st.session_state['wave_data']

# -----------------------------------------------------------------------------
# 3. 구글 시트 피드백 연결 (Teacher Feedback)
# -----------------------------------------------------------------------------
# 주의: secrets.toml 설정이 안 되어 있으면 에러가 나므로 예외처리함
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 데이터 읽기 (캐시 없이 즉시 로드 ttl=0)
    df_feedback = conn.read(worksheet="Feedback", ttl=0) 
except:
    conn = None
    df_feedback = pd.DataFrame(columns=["name", "message"])

# -----------------------------------------------------------------------------
# 4. 사이드바 (로그인 & 교사 모드)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("👤 분석관 정보")
    student_name = st.text_input("이름을 입력하세요", key="s_name")
    
    # [학생용] 피드백 확인 기능
    if student_name and conn:
        my_msg = df_feedback[df_feedback['name'] == student_name]['message'].values
        if len(my_msg) > 0:
            st.toast(f"🔔 선생님 메시지: {my_msg[-1]}", icon="👨‍🏫")
            st.info(f"👨‍🏫 **선생님 피드백:**\n\n{my_msg[-1]}")

    st.divider()
    
    # [교사용] 피드백 전송 패널
    with st.expander("🔐 선생님 전용 (Admin)"):
        pw = st.text_input("관리자 비밀번호", type="password")
        if pw == "1234":
            st.success("관리자 모드 접속")
            target_student = st.text_input("학생 이름 (받는 사람)")
            msg_content = st.text_area("보낼 메시지")
            
            if st.button("전송하기"):
                if conn and target_student:
                    # 새 데이터 추가
                    new_row = pd.DataFrame([{"name": target_student, "message": msg_content}])
                    updated_df = pd.concat([df_feedback, new_row], ignore_index=True)
                    conn.update(worksheet="Feedback", data=updated_df)
                    st.success(f"{target_student}에게 전송 완료!")
                else:
                    st.error("구글 시트가 연결되지 않았거나 이름이 비었습니다.")

# -----------------------------------------------------------------------------
# 5. 메인 UI
# -----------------------------------------------------------------------------
st.title("🌋 지진파 정밀 분석 센터 (Hard Mode)")

if st.session_state['stage'] == 'analysis':
    # [Phase 1] 그래프 분석 및 거리 계산
    st.subheader("STEP 1. 파형 분석 및 진원 거리 추론")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(t_data, wave_data, 'k-', lw=0.8, alpha=0.8, label='Seismogram')
        
        # 슬라이더 값 가져오기
        p_val = st.session_state.get('p_slider', 10.0)
        s_val = st.session_state.get('s_slider', 20.0)
        
        ax.axvline(p_val, c='blue', ls='--', label='P-Pick')
        ax.axvline(s_val, c='red', ls='--', label='S-Pick')
        if s_val > p_val:
            ax.axvspan(p_val, s_val, color='yellow', alpha=0.2)
        
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        
    with col2:
        st.markdown("##### 1️⃣ 파형 분석")
        p_in = st.slider("P파 도착(초)", 0.0, 100.0, 10.0, 0.1, key='p_slider')
        s_in = st.slider("S파 도착(초)", 0.0, 100.0, 20.0, 0.1, key='s_slider')
        
        st.markdown("##### 2️⃣ 거리 계산")
        # 힌트 제거됨
        user_dist = st.number_input("진원 거리(km)", min_value=0.0, step=1.0)
        
        if st.button("🚀 최종 제출"):
            # 오차 검증
            time_err = abs(p_in - true_p) + abs(s_in - true_s)
            dist_err = abs(user_dist - true_dist)
            
            # 허용 범위: 시간 합계 2.5초 이내, 거리 50km 이내
            if time_err < 2.5 and dist_err < 50.0:
                st.success("🏆 **분석 성공!** 정확합니다.")
                st.balloons()
                time.sleep(1)
                st.session_state['stage'] = 'quiz'
                st.rerun() # 퀴즈 화면으로 이동
            else:
                st.error("⚠️ **분석 실패**")
                if time_err >= 2.5:
                    st.write(f"❌ P파/S파 위치가 부정확합니다. (오차 합계가 큽니다)")
                if dist_err >= 50.0:
                    st.write(f"❌ 거리가 틀렸습니다. 공식을 다시 확인하세요.")

elif st.session_state['stage'] == 'quiz':
    # [Phase 2] 심화 문제 은행
    st.subheader("STEP 2. 수석 연구원 승급 시험")
    st.info("분석에 성공하신 것을 축하합니다! 랜덤 심화 문제를 풀어보세요.")
    
    # 새 문제 로드
    if st.session_state['current_quiz'] is None:
        st.session_state['current_quiz'] = random.choice(QUIZ_BANK)
        st.session_state['quiz_solved'] = False
    
    quiz = st.session_state['current_quiz']
    
    st.markdown(f"### Q. {quiz['q']}")
    
    # 정답 선택 UI
    choice = st.radio("정답을 선택하세요:", quiz['options'], key=f"q_{st.session_state.get('quiz_count', 0)}")
    
    col_a, col_b = st.columns([1, 4])
    with col_a:
        # 정답 확인 버튼
        if st.button("정답 확인"):
            if choice == quiz['a']:
                st.success("✅ 정답입니다!")
                st.session_state['quiz_solved'] = True
            else:
                st.error("❌ 틀렸습니다. 다시 생각해보세요.")
    
    with col_b:
        # 다음 문제 버튼 (정답을 맞혀야 활성화)
        if st.session_state['quiz_solved']:
            if st.button("➡️ 다음 문제 도전"):
                st.session_state['current_quiz'] = None # 초기화하여 새 문제 로드
                st.rerun()

    # 처음으로 돌아가기
    st.divider()
    if st.button("🔄 새로운 지진 데이터 분석하기 (처음으로)"):
        st.session_state['stage'] = 'analysis'
        del st.session_state['wave_data'] # 데이터 갱신
        st.rerun()
