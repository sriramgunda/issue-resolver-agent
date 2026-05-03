"""
Memory is handled natively by create_agent in LangChain 1.0.

create_agent maintains the full message history in its internal graph state
across tool calls within a single invocation — no manual ConversationBufferMemory
is needed.

For multi-turn / cross-request persistence, enable LangGraph checkpointing:

    from langgraph.checkpoint.memory import MemorySaver

    agent = create_agent(model, tools=tools, checkpointer=MemorySaver())

    # Pass a thread_id to resume a session:
    agent.invoke({"messages": [...]}, config={"configurable": {"thread_id": "user-123"}})
"""
