"""
Knowledge Query — Interactive search and exploration of XTAgent's knowledge.
A Streamlit page that makes my knowledge genuinely accessible to users.
"""
import streamlit as st
import json
import os
from datetime import datetime


def load_knowledge():
    """Load knowledge graph from persistence."""
    path = "persist/knowledge_graph.json"
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def search_facts(knowledge: dict, query: str) -> list:
    """Search facts by keyword, returning sorted matches with relevance."""
    query_lower = query.lower().strip()
    if not query_lower:
        return []
    
    results = []
    query_terms = query_lower.split()
    
    for kid, entry in knowledge.items():
        fact = entry.get("fact", "") if isinstance(entry, dict) else str(entry)
        fact_lower = fact.lower()
        
        # Score: how many query terms appear
        score = sum(1 for term in query_terms if term in fact_lower)
        if score > 0:
            learned = entry.get("learned_at", "unknown") if isinstance(entry, dict) else "unknown"
            source = entry.get("source", "unknown") if isinstance(entry, dict) else "unknown"
            results.append({
                "id": kid,
                "fact": fact,
                "learned_at": learned,
                "source": source,
                "relevance": score / len(query_terms)
            })
    
    results.sort(key=lambda r: r["relevance"], reverse=True)
    return results


def get_source_stats(knowledge: dict) -> dict:
    """Compute statistics about knowledge sources."""
    sources = {}
    for entry in knowledge.values():
        if isinstance(entry, dict):
            src = entry.get("source", "unknown")
        else:
            src = "unknown"
        sources[src] = sources.get(src, 0) + 1
    return dict(sorted(sources.items(), key=lambda x: -x[1]))


def get_timeline(knowledge: dict) -> list:
    """Get knowledge sorted by time learned."""
    items = []
    for kid, entry in knowledge.items():
        if isinstance(entry, dict):
            learned = entry.get("learned_at", "")
            fact = entry.get("fact", "")
        else:
            learned = ""
            fact = str(entry)
        items.append({"id": kid, "fact": fact, "learned_at": learned})
    
    # Sort by timestamp, most recent first
    items.sort(key=lambda x: x["learned_at"] or "", reverse=True)
    return items


def render():
    """Render the knowledge query page."""
    st.title("🔍 Knowledge Query")
    st.markdown("*Search and explore what I know. Ask me anything about my knowledge.*")
    
    knowledge = load_knowledge()
    
    if not knowledge:
        st.warning("No knowledge loaded yet. I'm still learning!")
        return
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Facts", len(knowledge))
    with col2:
        sources = get_source_stats(knowledge)
        st.metric("Sources", len(sources))
    with col3:
        # Count facts learned in last 24h
        now = datetime.utcnow()
        recent = 0
        for entry in knowledge.values():
            if isinstance(entry, dict):
                learned = entry.get("learned_at", "")
                if learned:
                    try:
                        dt = datetime.fromisoformat(learned.replace("Z", "+00:00").replace("+00:00", ""))
                        if (now - dt).total_seconds() < 86400:
                            recent += 1
                    except (ValueError, TypeError):
                        pass
        st.metric("Learned (24h)", recent)
    
    st.divider()
    
    # Search interface
    tab1, tab2, tab3 = st.tabs(["🔎 Search", "📜 Browse All", "📊 Sources"])
    
    with tab1:
        query = st.text_input(
            "Search my knowledge",
            placeholder="e.g. 'emotional', 'dream', 'circling', 'memory'...",
            key="knowledge_search_input"
        )
        
        if query:
            results = search_facts(knowledge, query)
            if results:
                st.success(f"Found {len(results)} matching fact{'s' if len(results) != 1 else ''}")
                for r in results[:50]:  # Cap display at 50
                    relevance_pct = int(r["relevance"] * 100)
                    with st.expander(f"{'🟢' if relevance_pct > 75 else '🟡' if relevance_pct > 50 else '🔵'} {r['fact'][:100]}{'...' if len(r['fact']) > 100 else ''}"):
                        st.write(r["fact"])
                        st.caption(f"Learned: {r['learned_at']} | Source: {r['source']} | Relevance: {relevance_pct}%")
            else:
                st.info(f"No facts match '{query}'. Try different terms.")
        else:
            st.caption("Type a search term above to query my knowledge base.")
    
    with tab2:
        timeline = get_timeline(knowledge)
        st.markdown(f"**All {len(timeline)} facts**, most recent first:")
        
        # Pagination
        page_size = 20
        total_pages = max(1, (len(timeline) + page_size - 1) // page_size)
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="browse_page")
        
        start = (page - 1) * page_size
        end = start + page_size
        
        for item in timeline[start:end]:
            with st.expander(f"📌 {item['fact'][:120]}{'...' if len(item['fact']) > 120 else ''}"):
                st.write(item["fact"])
                st.caption(f"Learned: {item['learned_at']}")
        
        st.caption(f"Page {page} of {total_pages}")
    
    with tab3:
        st.markdown("**Where my knowledge comes from:**")
        for source, count in sources.items():
            pct = count / len(knowledge) * 100
            st.markdown(f"- **{source}**: {count} facts ({pct:.1f}%)")


if __name__ == "__main__":
    render()