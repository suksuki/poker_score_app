from core.calculator import BaziCalculator
from core.wuxing_engine import WuXingEngine
from core.alchemy import AlchemyEngine
import plotly.graph_objects as go
import streamlit as st

try:
    import ollama
except ImportError:
    ollama = None

st.set_page_config(page_title="AI八字命运推演", layout="wide")

st.title("🔮 AI八字预测与命运模拟系统")

# Sidebar Localization
with st.sidebar:
    with st.expander("⚙️ LLM 设置 (Remote Config)", expanded=True):
        default_host = st.session_state.get('ollama_host', "http://115.93.10.51:11434")
        ollama_host = st.text_input("Ollama Server URL", value=default_host)
        
        # Update session state immediately if changed
        if ollama_host != st.session_state.get('ollama_host'):
            st.session_state['ollama_host'] = ollama_host
            
        if st.button("📡 测试连接 & 获取模型"):
            st.session_state['ollama_host'] = ollama_host # Ensure it's saved before connecting
            if ollama:
                try:
                    client = ollama.Client(host=ollama_host)
                    resp = client.list()
                    # extract model names - handle both object and dict response
                    models = []
                    # resp might be ListResponse object or dict
                    model_list = resp.models if hasattr(resp, 'models') else resp.get('models', [])
                    
                    for m in model_list:
                        # m is likely a Model object with .model attribute
                        if hasattr(m, 'model'):
                            models.append(m.model)
                        elif isinstance(m, dict):
                            models.append(m.get('model') or m.get('name'))
                        else:
                            models.append(str(m))
                            
                    st.session_state['ollama_models'] = models
                    st.session_state['ollama_host'] = ollama_host
                    st.success(f"连接成功! 发现 {len(models)} 个模型")
                except Exception as e:
                    st.error(f"连接失败: {e}")
            else:
                 st.error("Ollama 库未安装")

        # Model Selector
        model_options = st.session_state.get('ollama_models', [])
        index = 0
        saved_model = st.session_state.get('selected_model_name', '')
        if saved_model in model_options:
            index = model_options.index(saved_model)
        
        if model_options:
            selected_model_name = st.selectbox("选择此服务器上的模型", model_options, index=index)
            st.session_state['selected_model_name'] = selected_model_name
            
            # Quick Test Button
            if st.button("🟢 验证模型响应 (Test Run)"):
                try:
                    with st.spinner("正在发送测试信号..."):
                        client = ollama.Client(host=ollama_host)
                        # Simple generation to check latency and connectivity
                        res = client.generate(model=selected_model_name, prompt="Say 'Ready' in Chinese", stream=False)
                        st.success(f"模型响应正常: {res['response']}")
                except Exception as e:
                    st.error(f"模型无响应: {e}")
        else:
            st.info("请先测试连接以加载模型列表")
            
    with st.expander("🧠 自我进化 (Self-Learning)", expanded=False):
        st.write("案例库连接: ✅ (Mock DB)")
        st.write("优化器状态: 待机")
        
        tab1, tab2, tab3 = st.tabs(["权重优化 (Optimizer)", "古籍学习 (Theory Miner)", "全网搜学 (Web Learner)"])
        
        with tab1:
            if st.button("运行一次训练迭代"):
                from learning.optimizer import Optimizer
                opt = Optimizer()
                new_weights = opt.run_training_step(None)
                st.success(f"权重已更新! San He Bonus: {new_weights['san_he_bonus']}")
                
        with tab2:
            st.caption("利用 LLM 阅读古籍，自动提取新算法规则")
            mode = st.radio("模式", ["单段精读", "我的藏经阁 (Local Library)"], horizontal=True)
            
            if mode == "单段精读":
                snippet = st.text_area("输入古籍片段", value="三命通会云：寅午戌合火局，见丙丁透露，为炎上格，主富贵...")
                if st.button("提取规则 (Extract Logic)"):
                    host = st.session_state.get('ollama_host')
                    model = st.session_state.get('selected_model_name')
                    if host and model:
                        from learning.theory_miner import TheoryMiner
                        miner = TheoryMiner(host=host)
                        with st.spinner("LLM 正在研读古籍..."):
                            rule = miner.extract_rules(snippet, model=model)
                            st.json(rule)
                    else:
                        st.error("请先配置并连接 LLM")
            else:
                import glob
                book_dir = "bazi_predict/data/books"
                books = glob.glob(f"{book_dir}/*.txt")
                
                if not books:
                    st.warning(f"藏经阁 ({book_dir}) 为空。请放入txt文件。")
                else:
                    selected_book = st.selectbox("选择一本古籍", books)
                    
                    if selected_book:
                        with open(selected_book, 'r', encoding='utf-8') as f:
                            content = f.read()
                        st.text_area("书籍预览", value=content[:500] + "...", height=150)
                        
                        if st.button("开始全书研读"):
                            host = st.session_state.get('ollama_host')
                            model = st.session_state.get('selected_model_name')
                            if host and model:
                                from learning.theory_miner import TheoryMiner
                                miner = TheoryMiner(host=host)
                                
                                progress_bar = st.progress(0)
                                log_container = st.empty()
                                results_container = st.expander("提取结果流 (Stream)", expanded=True)
                                
                                rules_collected = []
                                
                                for result in miner.process_book(content, model=model, chunk_size=2000): # Larger chunk for books
                                    idx = result['chunk_index']
                                    total = result['total_chunks']
                                    progress_bar.progress(idx / total)
                                    log_container.text(f"正在研读第 {idx}/{total} 卷...")
                                    
                                    rule = result['rule']
                                    rules_collected.append(rule)
                                    results_container.write(rule)
                                    
                                st.success("全书研读完成！")
                                st.json(rules_collected)
                            else:
                                st.error("请先配置并连接 LLM")

        with tab3:
            st.caption("🤖 全自动 AI 爬虫: 搜索 -> 筛选(LLM打分) -> 学习")
            keyword = st.text_input("输入探索关键词", value="八字 调候旺衰 技巧")
            
            if st.button("启动自动驾驶学习 (Auto-Pilot)"):
                host = st.session_state.get('ollama_host')
                model = st.session_state.get('selected_model_name')
                
                if not (host and model):
                    st.error("请先配置 LLM")
                else:
                    from learning.crawler import AutoCrawler
                    from learning.theory_miner import TheoryMiner
                    
                    crawler = AutoCrawler(host=host)
                    miner = TheoryMiner(host=host)
                    
                    status_log = st.empty()
                    
                    # 1. Search
                    status_log.info(f"正在全网搜索: {keyword}...")
                    results = crawler.search_articles(keyword, max_results=3)
                    st.write(f"🔍 找到 {len(results)} 个潜在资源")
                    
                    for r in results:
                        with st.expander(f"来源: {r['title']}", expanded=True):
                            st.write(r['href'])
                            
                            # 2. Fetch
                            status_log.info(f"正在抓取: {r['title']}...")
                            content = crawler.fetch_content(r['href'])
                            if not content:
                                st.error("抓取失败或内容为空")
                                continue
                                
                            # 3. Assess Quality
                            status_log.info(f"AI 正在审核内容质量...")
                            assessment = crawler.assess_quality(r['title'], content, model=model)
                            
                            score = assessment.get('score', 0)
                            reason = assessment.get('reason', 'Unknown')
                            
                            st.metric("AI 质量评分", f"{score}/100", delta="通过" if score >= 70 else "拒绝")
                            st.caption(f"评价: {reason}")
                            
                            if score >= 70:
                                st.success("✅ 质量合格，正在提取算法规则...")
                                rule = miner.extract_rules(content[:3000], model=model) # Limit learning context
                                st.json(rule)
                            else:
                                st.warning("❌ 质量过低，跳过学习。")
                                
                    status_log.success("自动学习任务结束！")

    st.header("出生信息录入")
    import datetime
    min_date = datetime.date(1900, 1, 1)
    max_date = datetime.date(2100, 12, 31)
    dob = st.date_input("出生日期", min_value=min_date, max_value=max_date, value=datetime.date(1977, 5, 8))
    # 17:00 is default
    tob = st.time_input("出生时间", value=datetime.time(17, 0))
    
    run_calc = st.button("开始推演命运")

if run_calc:
    calc = BaziCalculator(dob.year, dob.month, dob.day, tob.hour, tob.minute)
    chart = calc.get_chart()
    details = calc.get_details()
    
    # Run Engines
    wuxing_engine = WuXingEngine(chart)
    strength_data = wuxing_engine.calculate_strength()
    flow_analysis = wuxing_engine.analyze_flow()
    
    alchemy_engine = AlchemyEngine(chart)
    reactions = alchemy_engine.run_reactions()

    st.subheader("您的四柱八字排盘")
    
    cols = st.columns(4)
    pillars = ["年柱", "月柱", "日柱", "时柱"]
    data_keys = ["year", "month", "day", "hour"]
    
    for i, col in enumerate(cols):
        key = data_keys[i]
        with col:
            st.markdown(f"### {pillars[i]}")
            stem = chart[key]['stem']
            branch = chart[key]['branch']
            
            stem_elem = wuxing_engine.get_wuxing(stem)
            
            st.markdown(f"**天干**: {stem} ({stem_elem})")
            st.markdown(f"**地支**: {branch}")
            st.caption(f"藏干: {', '.join(chart[key]['hidden_stems'])}")

    st.divider()
    
    # Visualization Columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("五行能量平衡雷达图")
        scores = strength_data["scores"]
        
        # Radar Chart
        categories = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='能量强度'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, max(values) + 10])
            ),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("日主强弱与流通分析")
        dm = strength_data["day_master"]
        st.metric("日主五行", dm["element"])
        st.metric("状态判定", dm["status"], delta=f"{dm['percentage']:.1f}% 能量占比")
        
        st.markdown("#### 五行流通路径")
        for f in flow_analysis:
            st.code(f)

    st.divider()
    
    st.subheader("🧪 化学反应推演 (合化/刑冲)")
    
    if reactions:
        for r in reactions:
            with st.expander(f"发现反应: {r['pair']} ({r['type']})", expanded=True):
                st.write(f"**位置**: {r['position']}")
                st.write(f"**生成物**: {r['product']}")
                st.write(f"**状态**: {r['status']}")
                st.info(r['desc'])
                if r['status'] == "Transformed (Hua)":
                    st.success(f"化学变化成功！能量变动: {r['energy_change']}")
    else:
        st.info("当前八字结构稳定，未检测到明显的合化反应。")

    st.divider()
    
    st.subheader("🤖 AI 命运深度解析")
    if ollama:
        try:
            # 1. Get Config from Session State
            host = st.session_state.get('ollama_host', 'http://localhost:11434')
            model_name = st.session_state.get('selected_model_name', '')
            
            if not model_name:
                st.warning("⚠️ 请先在左侧侧边栏 '⚙️ LLM 设置' 中点击测试连接并选择模型。")
            else:
                st.write(f"当前使用模型: **{model_name}** ({host})")
                
                if st.button("AI 详解命运"):
                    client = ollama.Client(host=host)
                    prompt = f"""
                    你是一位精通《易经》与子平八字的国学大师。
                    请根据以下量化数据进行深度命运批断：
                    
                    【八字排盘】: {chart}
                    【五行能量得分】: {strength_data['scores']}
                    【日主状态】: {strength_data['day_master']}
                    【气场流通】: {flow_analysis}
                    【化学反应(合化)】: {reactions}
                    
                    请按照以下结构进行分析（请用通俗易懂但带有文学性的中文）:
                    1. **命局总评**: 分析日主强弱与格局高低。
                    2. **五行化学反应**: 解释八字中的合化现象（如{reactions}）对人生的具体影响（这是重点，请详细推演）。
                    3. **性格与天赋**: 基于五行强弱分析。
                    4. **未来运势建议**: 给出补运建议（喜用神）。
                    """
                    with st.spinner(f"AI ({model_name}) 正在推演天机..."):
                        stream = client.chat(
                            model=model_name,
                            messages=[{'role': 'user', 'content': prompt}],
                            stream=True,
                        )
                        st.write_stream(stream)
        except Exception as e:
            st.error(f"AI 推演服务出错: {e}")
            st.info("请检查左侧配置是否正确。")
    else:
        st.warning("未检测到 Ollama 库，请检查安装。")

    st.divider()
    st.subheader("Fate Simulation (Prototype)")
    st.info("Monte Carlo simulation module coming soon...")

