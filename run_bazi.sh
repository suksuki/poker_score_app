#!/bin/bash
source bazi_predict/venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/bazi_predict
streamlit run bazi_predict/main.py --server.port 8501 --server.headless true
