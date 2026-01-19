import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. 초기 설정 및 문제 은행
# -----------------------------------------------------------------------------
st.set_page_config(page_title="지진파 분석", page_icon="🌋", layout="wide")

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
if 'stage' not in st.session_state: st.session_state['stage'] = 'analysis' 
if 'quiz_queue' not in st.session_state: st.session_state['quiz_queue'] = []
if 'quiz_solved' not in st.session_state: st.session_state['quiz_solved'] = False
if 'correct_count' not in st.session_state: st.session_state['correct_count'] = 0

# -----------------------------------------------------------------------------
# 2. 구글 시트 연결
# -----------------------------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df_fb = conn.read(worksheet="Feedback", ttl=0)
        if df_fb.empty or 'name' not in df_fb.columns:
             df_fb = pd.DataFrame(columns=["name", "message"])
        
        df_sc = conn.read(worksheet="Scoreboard", ttl=0)
        if df_sc.empty:
            df_sc = pd.DataFrame(columns=["name", "timestamp", "success", "time_err", "dist_err"])
            
        return df_fb, df_sc
    except Exception:
        return pd.DataFrame(columns=["name", "message"]), pd.DataFrame(columns=["name", "timestamp", "success", "time_err", "dist_err"])

df_feedback, df_scores = load_data()

# -----------------------------------------------------------------------------
# 3. 데이터 생성 함수 (진폭 수정됨)
# -----------------------------------------------------------------------------
def get_seismic_data():
    dist = np.random.randint(200, 500) 
    
    vp = 8.0  
    vs = 4.0  
    
    t = np.linspace(0, 100, 1000)
    tp = dist/vp + 5
    ts = dist/vs + 5
    
    # [수정됨] 진폭 설정
    noise_amp = 0.5
    p_amp = 2.5  # P파 진폭 2.5로 설정
    
    np.random.seed(int(time.time()))
    wave = np.random.normal(0, noise_amp, len(t))
    
    p_idx = int(tp * 10)
    if p_idx < len(t):
        length = min(150, len(t)-p_idx)
        wave[p_idx:p_idx+length] += np.sin(np.linspace(0, 10*np.pi, length)) * p_amp
    
    s_idx = int(ts * 10)
    if s_idx < len(t):
        length = min(200, len(t)-s_idx)
        # [수정됨] S파 진폭 배율 축소 (3.0 -> 2.2)
        wave[s_idx:s_idx+length] += np.sin(np.linspace(0, 10*np.pi, length)) * (p_amp * 2.2)
        
    return t, wave, tp, ts, dist

# 데이터 생성 또는 초기화
if 'wave_data' not in st.session_state:
    st.session_state['wave_data'] = get_seismic_data()

t_data, wave_data, true_p, true_s, true_dist = st.session_state['wave_data']

# -----------------------------------------------------------------------------
# 4. 사이드바
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("👤 학생 이름")
    student_name = st.text_input("이름", key="s_name")
    
    if student_name:
        my_msg_df = df_feedback[df_feedback['name'] == student_name]
        if not my_msg_df.empty:
            last_msg = my_msg_df.iloc[-1]['message']
            st.divider()
            st.toast(f"🔔 선생님 메시지 도착!", icon="👨‍🏫")
            st.info(f"👨‍🏫 **선생님 피드백:**\n\n{last_msg}")
        
        if st.button("📩 메시지 수신 확인"):
            st.rerun()

    st.divider()
    
    with st.expander("🔐 선생님 전용 (Admin)"):
        pw = st.text_input("관리자 비밀번호", type="password")
        if pw == "1234":
            st.success("관리자 모드 접속됨")
            
            st.markdown("### 📊 실시간 학생 현황")
            if st.button("🔄 현황 새로고침"):
                st.rerun()
                
            if not df_scores.empty:
                st.dataframe(df_scores.tail(10).iloc[::-1], hide_index=True)
            else:
                st.write("아직 제출된 기록이 없습니다.")
            
            st.divider()
            
            st.markdown("### 📨 피드백 전송")
            target_student = st.text_input("학생 이름 (받는 사람)")
            msg_content = st.text_area("보낼 내용")
            
            if st.button("전송하기"):
                if target_student and msg_content:
                    try:
                        new_msg = pd.DataFrame([{"name": target_student, "message": msg_content}])
                        updated_fb = pd.concat([df_feedback, new_msg], ignore_index=True)
                        conn.update(worksheet="Feedback", data=updated_fb)
                        st.success(f"To: {target_student} 전송 완료!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"전송 실패: {e}")

# -----------------------------------------------------------------------------
# 5. 메인 UI
# -----------------------------------------------------------------------------
st.title("🌋 지진파 분석")

if st.session_state['stage'] == 'analysis':
    st.subheader("STEP 1. 파형 분석 및 진원 거리 추론")
    st.markdown("P파와 S파의 시작점을 찾아 표시하고, 진원 거리를 계산하세요.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(t_data, wave_data, 'k-', lw=0.8, alpha=0.8)
        
        p_val = st.session_state.get('p_slider', 10.0)
        s_val = st.session_state.get('s_slider', 20.0)
        
        ax.axvline(p_val, c='blue', ls='--', label='P-wave')
        ax.axvline(s_val, c='red', ls='--', label='S-wave')
        if s_val > p_val:
            ax.axvspan(p_val, s_val, color='yellow', alpha=0.2)
            
        ax.set_xlabel("Time (sec)", fontsize=10)
        # [수정됨] Y축 라벨 변경
        ax.set_ylabel("Relative Amplitude", fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_xticks(np.arange(0, 101, 10))
        
        st.pyplot(fig)
        
    with col2:
        st.markdown("##### 1️⃣ 파형 분석")
        p_in = st.slider("P파 도착(초)", 0.0, 100.0, 10.0, 0.1, key='p_slider')
        s_in = st.slider("S파 도착(초)", 0.0, 100.0, 20.0, 0.1, key='s_slider')
        
        st.markdown("##### 2️⃣ 거리 계산")
        user_dist = st.number_input("진원 거리(km)", min_value=0.0, step=1.0)
        
        st.markdown("---")
        
        # [수정됨] 버튼 이름 변경 (최종 제출 -> 제출)
        if st.button("🚀 제출", type="primary"):
            if not student_name:
                st.error("⚠️ 먼저 사이드바에 '이름'을 입력해주세요!")
            else:
                time_err = abs(p_in - true_p) + abs(s_in - true_s)
                dist_err = abs(user_dist - true_dist)
                is_success = "Fail"
                
                if time_err < 2.5 and dist_err < 50.0:
                    st.success("🏆 **분석 성공!** 확인 문제로 이동합니다.")
                    st.balloons()
                    is_success = "Success"
                    time.sleep(1.5)
                    
                    st.session_state['stage'] = 'quiz'
                    st.session_state['quiz_queue'] = random.sample(QUIZ_BANK, 3)
                    st.session_state['correct_count'] = 0 
                    st.session_state['quiz_solved'] = False
                    st.rerun()
                else:
                    st.error(f"⚠️ **분석 실패** (시간오차: {time_err:.1f}s, 거리오차: {dist_err:.0f}km)")
                
                try:
                    now = datetime.now().strftime("%H:%M:%S")
                    new_score = pd.DataFrame([{
                        "name": student_name,
                        "timestamp": now,
                        "success": is_success,
                        "time_err": round(time_err, 2),
                        "dist_err": round(dist_err, 1)
                    }])
                    updated_scores = pd.concat([df_scores, new_score], ignore_index=True)
                    conn.update(worksheet="Scoreboard", data=updated_scores)
                except Exception as e:
                    st.warning("결과 저장 중 통신 오류 (잠시 후 다시 시도)")

    st.divider()
    if st.button("🔄 데이터 교체 (초기화)"):
        st.session_state['wave_data'] = get_seismic_data()
        st.rerun()

elif st.session_state['stage'] == 'quiz':
    st.subheader("STEP 2. 확인 문제")
    
    goal = 3
    current = st.session_state['correct_count']
    st.progress(current / goal, text=f"진행 상황: {current} / {goal} 문제 성공")
    
    if current < len(st.session_state['quiz_queue']):
        quiz = st.session_state['quiz_queue'][current]
        
        st.markdown(f"### Q. {quiz['q']}")
        
        choice = st.radio("정답 선택:", quiz['options'], key=f"q_radio_{current}")
        
        col_a, col_b = st.columns([1, 4])
        with col_a:
            if st.button("정답 확인"):
                if choice == quiz['a']:
                    st.success("✅ 정답입니다!")
                    if not st.session_state['quiz_solved']:
                        st.session_state['correct_count'] += 1
                        st.session_state['quiz_solved'] = True
                        st.rerun()
                else:
                    st.error("❌ 틀렸습니다. 다시 풀어보세요.")

        with col_b:
            if st.session_state['quiz_solved']:
                if st.session_state['correct_count'] < goal:
                    if st.button("➡️ 다음 문제"):
                        st.session_state['quiz_solved'] = False
                        st.rerun()
                else:
                    if st.button("🎉 미션 완료! (처음으로 돌아가기)"):
                        st.session_state['stage'] = 'analysis'
                        st.session_state['wave_data'] = get_seismic_data()
                        st.session_state['correct_count'] = 0
                        st.session_state['quiz_queue'] = []
                        st.rerun()
    else:
        if st.button("🎉 미션 완료! (처음으로 돌아가기)"):
            st.session_state['stage'] = 'analysis'
            st.session_state['wave_data'] = get_seismic_data()
            st.session_state['correct_count'] = 0
            st.rerun()
