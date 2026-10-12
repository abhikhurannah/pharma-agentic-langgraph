from time import perf_counter
from langgraph.graph import StateGraph, END
from backend.models import GraphState
from backend.tools import generate_report


def build_graph(store):
    def retrieve(state):
        start = perf_counter()
        papers = store.search(f"{state['drug']} {state['disease']}", state['top_k'], state['source'])
        return {'papers': papers, 'trace': [{'stage': 'retrieve', 'duration_ms': round((perf_counter()-start)*1000), 'count': len(papers)}]}

    def report(state):
        start = perf_counter()
        text, mode, warnings = generate_report(state)
        if any(p['source'] == 'demo' for p in state['papers']):
            warnings.append('Synthetic demo data: findings and numbers are fictional, not published evidence.')
        return {'final_report': text, 'generation_mode': mode, 'warnings': warnings,
                'summaries': [], 'trace': state['trace'] + [{'stage': 'generate', 'duration_ms': round((perf_counter()-start)*1000)}]}

    graph = StateGraph(GraphState)
    graph.add_node('retrieve', retrieve)
    graph.add_node('report', report)
    graph.set_entry_point('retrieve')
    graph.add_edge('retrieve', 'report')
    graph.add_edge('report', END)
    return graph.compile()
