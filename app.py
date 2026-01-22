import streamlit as st
import numpy as np
import plotly.graph_objects as go 
import folium 
from streamlit_folium import st_folium 

# [설정] 페이지 기본 설정
st.set_page_config(layout="wide", page_title="AI 지진 연구소")

# [세션 상태 초기화]
if 'stage' not in st.session_state:
    st.session_state['stage'] = 1  # 1: 기초, 2: 심화
if 'distances' not in st.session_state:
    st.session_state['distances'] = {} 
if 'stage1_success' not in st.session_state:
    st.session_state['stage1_success'] = False # 1단계 성공 여부 저장

# --- 1. 기능 함수 정의 ---
def draw_interactive_graph(station_name, true_distance):
    t = np.linspace(0, 100, 1000)
    vp, vs = 8, 4
    tp = true_distance / vp
    ts = true_distance / vs
    
    # 파형 생성
    wave = np.sin(2 * np.pi * (t - tp)) * np.exp(-0.1 * (t - tp)) * (t > tp)
    wave += 2.5 * np.sin(2 * np.pi * (t - ts)) * np.exp(-0.1 * (t - ts)) * (t > ts)
    noise = np.random.normal(0, 0.1, size=len(t))
    final_wave = wave + noise

    # Plotly 그래프
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=final_wave, mode='lines', name=f'{station_name}', line=dict(color='black', width=1)))
    
    fig.update_layout(
        title=f"📊 {station_name} 지진계 (마우스를 올려 시간을 확인하세요)",
        xaxis_title="시간 (초)",
        yaxis_title="진폭",
        hovermode="x unified",
        dragmode="zoom",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    return tp, ts 

# --- 2. 메인 로직 ---

st.title("🌋 AI 지진 연구소: 진앙을 찾아라!")

# [Stage 1] 기초 훈련
if st.session_state['stage'] == 1:
    st.header("Step 1. 지진파 분석 기초 훈련")
    st.info("💡 미션: 그래프를 확대하여 P파와 S파가 도착한 시간을 정확히 찾고 거리를 계산하세요.")
    
    tp, ts = draw_interactive_graph("훈련용 관측소", 300)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        user_tp = st.number_input("P파 도착 시간(초)", min_value=0.0, step=0.1, format="%.1f")
    with col2:
        user_ts = st.number_input("S파 도착 시간(초)", min_value=0.0, step=0.1, format="%.1f")
    
    # 계산 버튼
    if st.button("거리 계산 확인"):
        ps_time = user_ts - user_tp
        cal_distance = ps_time * 8 
        error = abs(cal_distance - 300)
        
        if error < 10: # 오차 범위 10km로 조금 더 엄격하게
            st.success(f"✅ 정답입니다! (계산된 거리: {cal_distance:.1f}km)")
            st.balloons()
            st.session_state['stage1_success'] = True # 성공 상태 저장
        else:
            st.error(f"❌ 오차가 큽니다. (오차: {error:.1f}km) 다시 측정해보세요!")
            st.session_state['stage1_success'] = False

    # 성공했을 때만 다음 단계 버튼 보이기
    if st.session_state['stage1_success']:
        if st.button("🚀 레벨 업! 진앙 찾기 미션 시작"):
            st.session_state['stage'] = 2
            st.rerun()

# [Stage 2] 심화 미션
elif st.session_state['stage'] == 2:
    st.header("Step 2. 긴급 미션: 진앙을 추적하라!")
    st.warning("⚠️ 서울, 강릉, 부산 관측소 데이터를 분석하여 지도에 표시하세요.")
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📍 서울", "📍 강릉", "📍 부산", "🗺️ 지도 확인"])
    
    # 데이터 (예시)
    data = {
        "서울": {"dist": 320, "coords": [37.56, 126.97]},
        "강릉": {"dist": 200, "coords": [37.75, 128.87]},
        "부산": {"dist": 400, "coords": [35.17, 129.07]}
    }
    
    # 각 관측소 탭 로직
    for name, tab in zip(["서울", "강릉", "부산"], [tab1, tab2, tab3]):
        with tab:
            st.subheader(f"{name} 관측소 데이터 분석")
            # 그래프 그리기
            draw_interactive_graph(name, data[name]["dist"])
            
            # 입력 받기
            st.write("👇 그래프를 보고 거리를 계산해 입력하세요.")
            d = st.number_input(f"{name} 진원 거리(km)", key=f"dist_{name}", step=10)
            st.session_state['distances'][name] = d

    # 지도 탭 로직
    with tab4:
        st.subheader("최종 분석 결과")
        if st.button("진앙 추적 결과 보기"):
            m = folium.Map(location=[36.5, 127.5], zoom_start=7)
            
            all_input = True
            for name, info in data.items():
                radius = st.session_state['distances'].get(name, 0)
                if radius == 0:
                    st.warning(f"{name} 관측소의 거리가 입력되지 않았습니다.")
                    all_input = False
                
                # 관측소 표시
                folium.Marker(info['coords'], tooltip=name, icon=folium.Icon(color='blue', icon='star')).add_to(m)
                # 원 그리기 (미터 단위 변환)
                folium.Circle(
                    location=info['coords'],
                    radius=radius * 1000, 
                    color='red',
                    fill=True,
                    fill_opacity=0.2
                ).add_to(m)
            
            if all_input:
                st.success("세 원이 겹치는 곳이 진앙입니다! 겹치지 않는다면 거리를 다시 계산해보세요.")
            
            st_folium(m, width=700, height=500)
            
            # 처음으로 돌아가기 버튼
            if st.button("🔄 처음부터 다시 하기"):
                st.session_state['stage'] = 1
                st.session_state['stage1_success'] = False
                st.rerun()
