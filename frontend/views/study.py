import streamlit as st
import pandas as pd

from api.client import ApiClient


def render_study_goals(
    api: ApiClient
) -> None:
    st.header("학습 목표 관리")
    st.caption("목표 점수와 시험 날짜를 설정하고, 현재 상태와 비교해 학습 전략을 생성합니다.")
    
    goal_subject = st.selectbox(
        "목표 과목",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="goal_subject",
    )
    
    st.subheader("새 학습 목표 만들기")
    
    goal_title =  st.text_input(
        "목표 제목",
        value=f"{goal_subject} 시험 목표",
        key="goal_title",
    )
    
    target_score = st.slider(
        "목표 점수",
        min_value=0,
        max_value=100,
        value=85,
        key="target_score",
    )
    
    exam_date = st.date_input(
        "시험 날짜",
        key="goal_exam_date",
    )
    
    if st.button("학습 목표 생성하기"):
        response = api.post(
            "/study-goals",
            json={
                "subject": goal_subject,
                "title": goal_title,
                "target_score": target_score,
                "exam_date": str(exam_date),
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.success("학습 목표가 생성되었습니다.")
            st.write(result["goal"])
        else:
            st.error("학습 목표 생성에 실패했습니다.")
            st.write(response.text)
            
    st.divider()
    st.subheader("내 학습 목표 조회")
    
    if "study_goals" not in st.session_state:
        st.session_state.study_goals = []
        
    if st.button("학습 목표 목록 불러오기"):
        response = api.get(
            "/study-goals",
            params={
                "subject": goal_subject,
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.study_goals = result.get("goals", [])
            
            if not st.session_state.study_goals:
                st.info("등록된 학습 목표가 없습니다.")
            else:
                st.success(f"{result['goal_count']}개 목표를 불러왔습니다.")
        else:
            st.error("학습 목표 목록을 불러오지 못했습니다.")
            st.write(response.text)
            
    if st.session_state.study_goals:
        goal_options = {
            f"{goal['id']} / {goal['title']} / 목표 {goal['target_score']}점 / D-{goal['days_left']}": goal[
                "id"
            ]
            for goal in st.session_state.study_goals
        }
        
        selected_goal_label = st.selectbox(
            "분석할 목표 선택",
            list(goal_options.keys()),
            key="selected_goal_label",
        )
        
        selected_goal_id = goal_options[selected_goal_label]
        
        if st.button("목표 상태 분석하기"):
            response = api.get(
                "/study-goals/{selected_goal_id}/status",
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                
                goal = result["goal"]
                status = result["current_status"]
                
                st.subheader("목표 상태")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("목표 점수", goal["target_score"])
                with col2:
                    st.metric("남은 날짜", goal["days_left"])
                with col3:
                    st.metric("현재 평균", status["current_average_score"])
                with col4:
                    st.metric("목표까지 차이", status["score_gap"])
                    
                st.subheader("취약 개념")
                weak_concepts = result.get("weak_concepts", [])
                
                if not weak_concepts:
                    st.info("취약 개념 데이터가 없습니다.")
                else:
                    for item in weak_concepts:
                        st.write(f"- {item['concept']}: 오답 {item['wrong_count']}회")
            else:
                st.error("목표 상태 분석에 실패했습니다.")
                st.write(response.text)
                
        if st.button("AI 목표 달성 전략 생성하기"):
            response = api.post(
                "/study-goals/strategy",
                json={
                    "goal_id": selected_goal_id,
                },
                timeout=180,
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.success("목표 달성 전략이 생성되었습니다.")
                
                goal = result["goal"]
                status = result["current_status"]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("목표 점수", goal["target_score"])
                with col2:
                    st.metric("남은 날짜", goal["days_left"])
                with col3:
                    st.metric("현재 평균", status["current_average_score"])
                with col4:
                    st.metric("목표까지 차이", status["score_gap"])
                    
                st.subheader("AI 목표 달성 전략")
                st.markdown(result["strategy"])
                
                st.download_button(
                    label="목표 달성 전략 Markdown 다운로드",
                    data=result["strategy"],
                    file_name="goal_strategy.md",
                    mime="text/markdown",
                )
            else:
                st.error("목표 달성 전략 생성에 실패했습니다.")
                st.write(response.text)
                
                
def render_goal_dashboard(
    api: ApiClient,
) -> None:
    st.header("목표별 대시보드")
    st.caption("학습 목표를 기준으로 체크리스트, 학습 세션, 응시 기록, 취약 개념을 통합해서 보여줍니다.")
    
    dashboard_subject = st.selectbox(
        "대시보드 과목",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="dashboard_subject",
    )
    
    if "dashboard_goals" not in st.session_state:
        st.session_state.dashboard_goals = []
        
    if st.button("대시보드용 목표 목록 불러오기"):
        response = api.get(
            "/study-goals",
            params={
                "subject": dashboard_subject,
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.dashboard_goals = result.get("goals", [])
            
            if not st.session_state.dashboard_goals:
                st.info("등록된 학습 목표가 없습니다.")
            else:
                st.success(f"{result['goal_count']}개 목표를 불러왔습니다.")
        else:
            st.error("목표 목록을 불러오지 못했습니다.")
            st.write(response.text)
            
    if st.session_state.dashboard_goals:
        goal_options = {
            f"{goal['id']} / {goal['title']} / 목표 {goal['target_score']}점 / D-{goal['days_left']}": goal[
                "id"
            ]
            for goal in st.session_state.dashboard_goals
        }
        
        selected_goal_label = st.selectbox(
            "대시보드로 볼 목표 선택",
            list(goal_options.keys()),
            key="dashboard_goal_label",
        )
        
        selected_dashboard_goal_id = goal_options[selected_goal_label]
        
        if st.button("목표 대시보드 생성하기"):
            response = api.post(
                "/goal-dashboard",
                json={
                    "goal_id": selected_dashboard_goal_id,
                },
                timeout=180,
            )
            
            if response.status_code == 200:
                result = response.json()
                
                goal = result["goal"]
                checklist_summary = result["checklist_summary"]
                session_summary = result["session_summary"]
                attempt_summary = result["attempt_summary"]
                
                st.success("목표 대시보드가 생성되었습니다.")
                
                st.subheader("목표 정보")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("목표 점수", goal["target_score"])
                with col2:
                    st.metric("남은 날짜", goal["days_left"])
                with col3:
                    st.metric("최근 점수", attempt_summary["latest_score"])
                with col4:
                    st.metric("목표까지 차이", attempt_summary["score_gap"])
                    
                st.subheader("실행 현황")
                
                col5, col6, col7, col8 = st.columns(4)
                
                with col5:
                    st.metric("체크리스트 진행률", f"{checklist_summary['progress_rate']}%")
                with col6:
                    st.metric("완료 항목", checklist_summary["done_count"])
                with col7:
                    st.metric("총 공부 시간", f"{session_summary['total_hours']}시간")
                with col8:
                    st.metric("평균 집중도", session_summary["avg_focus_score"])
                    
                st.progress(checklist_summary["progress_rate"] / 100)
                
                st.subheader("응시 요약")
                
                col9, col10, col11 = st.columns(3)
                                
                with col9:
                    st.metric("응시 횟수", attempt_summary["attempt_count"])
                with col10:
                    st.metric("평균 점수", attempt_summary["avg_score"])
                with col11:
                    st.metric("최고 점수", attempt_summary["best_score"])
                    
                st.subheader("취약 개념")
                
                weak_concepts = result.get("weak_concepts", [])
                
                if not weak_concepts:
                    st.info("취약 개념 데이터가 없습니다.")
                else:
                    for item in weak_concepts:
                        st.write(f"- {item['concept']}: 오답 {item['wrong_count']}회")
                        
                st.subheader("최근 학습 세션")
                
                recent_sessions = session_summary.get("recent_sessions", [])
                
                if not recent_sessions:
                    st.info("이 목표에 연결된 학습 세션이 없습니다.")
                else:
                    for session in recent_sessions:
                        with st.expander(
                            f"{session['duration_minutes']}분 / 집중도 {session['focus_score']} / {session['created_at']}"
                        ):
                            st.write("공부 내용")
                            st.write(session["content"])
                            
                            if session["reflection"]:
                                st.write("회고")
                                st.write(session["reflection"])
                                
                st.subheader("최근 응시 기록")
                
                recent_attempts = attempt_summary.get("recent_attempts", [])
                
                if not recent_attempts:
                    st.info("이 과목의 응시 기록이 없습니다.")
                else:
                    for attempt in recent_attempts:
                        st.write(
                            f"- {attempt['title']} / {attempt['score']}점 "
                            f"({attempt['correct_count']}/{attempt['total_questions']})"
                        )
                        
                st.subheader("AI 목표 상태 코멘트")
                st.markdown(result["comment"])
                
                st.download_button(
                    label="목표 대시보드 코멘트 다운로드",
                    data=result["comment"],
                    file_name="goal_dashboard_comment.md",
                    mime="text/markdown",
                )
            else:
                st.error("목표 대시보드 생성에 실패했습니다.")
                st.write(response.text)
                
                
def render_smart_review(
    api: ApiClient,
) -> None:
    st.header("스마트 복습 큐")
    st.caption("오답, 응시 기록, 체크리스트, 학습 세션을 종합해 오늘 복습할 항목을 추천합니다.")
    
    smart_subject = st.selectbox(
        "복습 큐 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="smart_review_subject",
    )
    
    smart_limit = st.slider(
        "추천 항목 수",
        min_value=1,
        max_value=10,
        value=5,
        key="smart_review_limit",
    )
    
    if st.button("오늘의 스마트 복습 큐 생성하기"):
        payload = {
            "limit": smart_limit,
        }
        
        if smart_subject != "전체":
            payload["subject"] = smart_subject
            
        response = api.post(
            "/smart-review/queue/save",
            json=payload,
            timeout=180,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            st.success("스마트 복습 큐가 생성되었습니다.")
            
            session_summary = result["session_summary"]
            attempt_summary = result["attempt_summary"]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("최근 7일 학습 시간", f"{session_summary['total_hours']}시간")
            with col2:
                st.metric("최근 7일 세션 수", session_summary["session_count"])
            with col3:
                st.metric("최근 7일 응시 수", attempt_summary["attempt_count"])
            with col4:
                st.metric("최근 점수", attempt_summary["latest_score"])
                
            st.subheader("취약 개념")
            weak_concepts = result.get("weak_concepts", [])
            
            if not weak_concepts:
                st.info("취약 개념 데이터가 없습니다.")
            else:
                for item in weak_concepts[:5]:
                    st.write(f"- {item['concept']}: 오답 {item['wrong_count']}회")
                    
            st.subheader("미완료 체크리스트")
            pending_checklists = result.get("pending_checklists", [])
            
            if not pending_checklists:
                st.info("미완료 체크리스트가 없습니다.")
            else:
                for item in pending_checklists[:5]:
                    st.write(f"- P{item['priority']} / {item['title']}")
                    
            st.subheader("AI 오늘의 복습 큐")
            st.markdown(result["queue"])
            
            st.download_button(
                label="스마트 복습 큐 Markdown 다운로드",
                data=result["queue"],
                file_name="smart_review_queue.md",
                mime="text/markdown",
            )
        else:
            st.error("스마트 복습 큐 생성에 실패했습니다.")
            st.write(response.text)

    include_done = st.checkbox(
        "완료 항목 포함",
        value=True,
        key="smart_review_include_done",
    )
    
    if st.button("저장된 스마트 복습 큐 불러오기"):
        params = {
            "include_done": include_done,
            "limit": 30,
        }
        
        if smart_subject != "전체":
            params["subject"] = smart_subject
            
        response = api.get(
            "/smart-review/queue/items",
            params=params,
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.smart_review_items = result.get("items", [])
            st.session_state.smart_review_progress = {
                "total_count": result["total_count"],
                "done_count": result["done_count"],
                "progress_rate": result["progress_rate"],
            }
        else:
            st.error("저장된 스마트 복습 큐를 불러오지 못했습니다.")
            st.write(response.text)
            
    if "smart_review_progress" in st.session_state:
        progress = st.session_state.smart_review_progress
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("큐 항목 수", progress["total_count"])
        with col2:
            st.metric("완료 항목", progress["done_count"])
        with col3:
            st.metric("완료율", f"{progress['progress_rate']}%")
            
        st.progress(progress["progress_rate"] / 100)
        
    if "smart_review_items" not in st.session_state:
        st.session_state.smart_review_items = []
        
    for item in st.session_state.smart_review_items:
        status_icon = "✅" if item["is_done"] else "⬜"
        
        with st.expander(
            f"{status_icon} P{item['priority']} / {item['title']}"
        ):
            st.write("추천 이유")
            st.write(item['reason'])
            
            st.write("실행 방법")
            st.write(item["action"])
            
            st.caption(
                f"source_type={item['source_type']} / "
                f"estimated={item['estimated_minutes']}분 / "
                f"subject={item['subject']}"
            )
            
            new_done = st.checkbox(
                "완료",
                value=item["is_done"],
                key=f"smart_review_done_{item['id']}",
            )
            
            if st.button(
                f"복습 큐 상태 저장 item_id={item['id']}",
                key=f"save_smart_review_{item['id']}",
            ):
                response = api.patch(
                    "/smart-review/queue/items/{item['id']}",
                    json={
                        "is_done": new_done,
                    },
                    timeout=30,
                )
                
                if response.status_code == 200:
                    st.success("복습 큐 상태가 저장되었습니다.")
                else:
                    st.error("복습 규 상태 저장에 실패했습니다.")
                    st.write(response.text)
                    
                    
def render_study_checklists(
    api: ApiClient,
) -> None:
    st.header("학습 체크리스트")
    st.caption("학습 목표를 바탕으로 실행 가능한 할 일을 생성하고 완료 상태를 관리합니다.")
    
    checklist_subject = st.selectbox(
        "체크리스트 과목",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="checklist_subject",
    )
    
    if "checklist_goals" not in st.session_state:
        st.session_state.checklist_goals = []
        
    if st.button("체크리스트용 목표 목록 불러오기"):
        response = api.get(
            "/study-goals",
            params={
                "subject": checklist_subject,
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.checklist_goals = result.get("goals", [])
            
            if not st.session_state.checklist_goals:
                st.info("등록된 학습 목표가 없습니다. 먼저 학습 목표를 생성하세요.")
            else:
                st.success(f"{result['goal_count']}개 목표를 불러왔습니다.")
        else:
            st.error("학습 목표 목록을 불러오지 못했습니다.")
            st.write(response.text)
            
    selected_checklist_goal_id = None
    
    if st.session_state.checklist_goals:
        goal_options = {
            f"{goal['id']} / {goal['title']} / 목표 {goal['target_score']}점 / D-{goal['days_left']}": goal[
                "id"
            ]
            for goal in st.session_state.checklist_goals
        }
        
        selected_goal_label = st.selectbox(
            "체크리스트를 만들 목표 선택",
            list(goal_options.keys()),
            key="checklist_goal_label",
        )
        
        selected_checklist_goal_id = goal_options[selected_goal_label]
        
        item_count = st.slider(
            "생성할 체크리스트 항목 수",
            min_value=3,
            max_value=10,
            value=5,
            key="checklist_item_count",
        )
        
        if st.button("AI 체크리스트 생성하기"):
            response = api.post(
                "/study-checklists/generate",
                json={
                    "goal_id": selected_checklist_goal_id,
                    "item_count": item_count,
                },
                timeout=180,
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"{result['item_count']}개 체크리스트가 생성되었습니다.")
            else:
                st.error("체크리스트 생성에 실패했습니다.")
                st.write(response.text)
                
    st.divider()
    st.subheader("내 체크리스트")
    
    if st.button("체크리스트 불러오기"):
        params = {
            "subject": checklist_subject,
        }
        
        if selected_checklist_goal_id is not None:
            params["goal_id"] = selected_checklist_goal_id
            
        response = api.get(
            "/study-checklists",
            params=params,
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.checklist_items = result.get("items", [])
            st.session_state.checklist_progress = {
                "total_count": result["total_count"],
                "done_count": result["done_count"],
                "progress_rate": result["progress_rate"],
            }
        else:
            st.error("체크리스트를 불러오지 못했습니다.")
            st.write(response.text)
            
    if "checklist_items" not in st.session_state:
        st.session_state.checklist_items = []
        
    if "checklist_progress" in st.session_state:
        progress = st.session_state.checklist_progress
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("전체 항목", progress["total_count"])
        with col2:
            st.metric("완료 항목", progress["done_count"])
        with col3:
            st.metric("진행률", f"{progress['progress_rate']}%")
            
        st.progress(progress["progress_rate"] / 100)
        
    for item in st.session_state.checklist_items:
        with st.expander(
            f"{'✅' if item['is_done'] else '⬜'} "
            f"P{item['priority']} / {item['title']}"
        ):
            st.write(item["description"])
            st.caption(f"과목: {item['subject']} / goal_id={item['goal_id']}")
            
            new_done = st.checkbox(
                "완료",
                value=item["is_done"],
                key=f"checklist_done_{item['id']}",
            )
            
            if st.button(
                f"상태 저장 item_id={item['id']}",
                key=f"save_checklist_{item['id']}",
            ): 
                response = api.patch(
                    f"/study-checklists/{item['id']}",
                    json={
                        "is_done": new_done,
                    },
                    timeout=30,
                )
                
                if response.status_code == 200:
                    st.success("체크리스트 상태가 저장되었습니다.")
                else:
                    st.error("체크리스트 상태 저장에 실패했습니다.")
                    st.write(response.text)
                    
                    
def render_study_sessions(
    api: ApiClient
) -> None:
    st.header("학습 세션 기록")
    st.caption("실제로 공부한 시간, 내용, 회고를 기록합니다.")
    
    session_subject = st.selectbox(
        "학습 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="session_subject",
    )
    
    duration_minutes= st.number_input(
        "공부 시간(분)",
        min_value=1,
        value=60,
        key="session_duration_minutes",
    )
    
    session_content = st.text_area(
        "공부한 내용",
        height=120,
        placeholder="예: 프로세스와 스레드 차이 복습, RAG 문제 5개 풀이",
        key="session_content",
    )
    
    session_reflection = st.text_area(
        "회고",
        height=100,
        placeholder="예: 스레드 동기화 개념이 아직 헷갈림",
        key="session_reflection",
    )
    
    focus_score = st.slider(
        "집중도",
        min_value=1,
        max_value=5,
        value=3,
        key="session_focus_score",
    )
    
    st.subheader("목표/체크리스트 연결 선택")
    
    linked_goal_id = None
    linked_checklist_item_id = None
    
    if "session_goals"  not in st.session_state:
        st.session_state.session_goals = []
        
    if st.button("세션 연결용 목표 목록 불러오기"):
        response = api.get(
            "/study-goals",
            params={
                "subject": session_subject,
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.session_goals = result.get("goals", [])
            
            if not st.session_state.session_goals:
                st.info("연결할 학습 목표가 없습니다.")
            else:
                st.success(f"{result['goal_count']}개 목표를 불러왔습니다.")
        else:
            st.error("학습 목표 목록을 불러오지 못했습니다.")
            st.write(response.text)
            
    if st.session_state.session_goals:
        goal_options = {
            "연결 안 함": None,
            **{
                f"{goal['id']} / {goal['title']} / 목표 {goal['target_score']}점": goal["id"]
                for goal in st.session_state.session_goals
            },
        }
        
        selected_goal_label = st.selectbox(
            "연결할 목표",
            list(goal_options.keys()),
            key="session_goal_label",
        )
        
        linked_goal_id = goal_options[selected_goal_label]
        
    if "session_checklist_items" not in st.session_state:
        st.session_state.session_checklist_items = []
        
    if st.button("세션 연결용 체크리스트 불러오기"):
        params = {
            "subject": session_subject,
        }
        
        if linked_goal_id is not None:
            params["goal_id"] = linked_goal_id
            
        response = api.get(
            "/study-checklists",
            params=params,
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.session_checklist_items = result.get("items", [])
            
            if not st.session_state.session_checklist_items:
                st.info("연결할 체크리스트가 없습니다.")
            else:
                st.success(f"{result['total_count']}개 체크리스트 항목을 불러왔습니다.")
        else:
            st.error("체크리스트를 불러오지 못했습니다.")
            st.write(response.text)
            
    if st.session_state.session_checklist_items:
        checklist_options = {
            "연결 안 함": None,
            **{
                f"{item['id']} / {'완료' if item['is_done'] else '미완료'} / {item['title']}": item[
                    "id"
                ]
                for item in st.session_state.session_checklist_items
            },
        }
        
        selected_checklist_label = st.selectbox(
            "연결할 체크리스트",
            list(checklist_options.keys()),
            key="session_checklist_label",
        )
        
        linked_checklist_item_id = checklist_options[selected_checklist_label]
        
    if st.button("학습 세션 저장하기"):
        if not session_content.strip():
            st.warning("공부한 내용을 입력하세요.")
        elif session_subject == "전체":
            st.warning("학습 세션 저장 시에는 구체적인 과목을 선택하세요.")
        else:
            payload = {
                "subject": session_subject,
                "goal_id": linked_goal_id,
                "checklist_item_id": linked_checklist_item_id,
                "duration_minutes": int(duration_minutes),
                "content": session_content,
                "reflection": session_reflection,
                "focus_score": focus_score,
            }
            
            response = api.post(
                "/study-sessions",
                json=payload,
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success("학습  세션이 저장되었습니다.")
                st.write(result["session"])
            else:
                st.error("학습 세션 저장에 실패했습니다.")
                st.write(response.text)
                
    st.divider()
    st.subheader("학습 세션 요약")
    
    if st.button("학습 세션 요약 불러오기"):
        params = {
        }
        
        if session_subject != "전체":
            params["subject"] = session_subject
        
        response = api.get(
            "/study-sessions/summary",
            params=params,
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("세션 수", result["session_count"])
            with col2:
                st.metric("총 공부 시간", f"{result['total_hours']}시간")
            with col3:
                st.metric("평균 집중도", result["avg_focus_score"])
                
            st.subheader("과목별 학습 시간")
            if result["subject_summary"]:
                st.dataframe(pd.DataFrame(result["subject_summary"]), use_container_width=True)
            else:
                st.info("학습 세션 데이터가 없습니다.")
        else:
            st.error("학습 세션 요약을 불러오지 못했습니다.")
            st.write(response.text)
            
    st.divider()
    st.subheader("최근 학습 세션")
    
    if st.button("최근 학습 세션 불러오기"):
        response = api.get(
            "/study-sessions",
            params={
                "subject": session_subject,
                "limit": 20,
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if not result["sessions"]:
                st.info("최근 학습 세션이 없습니다.")
            else:
                for session in result["sessions"]:
                    with st.expander(
                        f"{session['subject']} / {session['duration_minutes']}분 / {session['created_at']}"
                    ):
                        st.write("공부한 내용")
                        st.write(session["content"])
                        
                        if session["reflection"]:
                            st.write("회고")
                            st.write(session["reflection"])
                            
                        st.write(f"집중도: {session['focus_score']}")
                        st.caption(
                            f"goal_id={session['goal_id']} / checklist_item_id={session['checklist_item_id']}"
                        )
        else:
            st.error("최근 학습 세션을 불러오지 못했습니다.")
            st.write(response.text)
