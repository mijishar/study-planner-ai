"""Debug script: send 'hi' through chat() and show the real exception."""
import traceback
import sys
sys.path.insert(0, '.')

# Temporarily patch the exception handler to re-raise
import agent.agent as mod

_original_chat = mod.HackathonAgent.chat

def _debug_chat(self, message, session_id="default", images=None):
    import time
    t0 = time.perf_counter()
    # 1. Get / create session state
    agent_inst, selector, guard, ctx = self._session(session_id)

    # 2. Rebuild system prompt
    from decider_kit.llm import agent_model, image_blocks, strip_thinking
    from strands import Agent
    base_prompt = mod._EAGER_SYSTEM_PROMPT if self.eager else mod._BASE_SYSTEM_PROMPT
    fragment = ctx.to_prompt_fragment()
    system_prompt = f"{base_prompt}\n\n{fragment}" if fragment else base_prompt

    guard_before    = len(guard.log)
    selector_before = len(selector.log)

    print(f"\n[DEBUG] Calling selector.tools_for('{message}')")
    try:
        narrowed_tools = selector.tools_for(message)
        print(f"[DEBUG] narrowed_tools = {[getattr(t,'tool_name',str(t)) for t in narrowed_tools]}")
    except Exception as e:
        print(f"[DEBUG] selector.tools_for FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        return

    print(f"[DEBUG] Creating Agent and calling it")
    try:
        agent_with_tools = Agent(
            model=agent_model(self.model_id),
            system_prompt=system_prompt,
            tools=narrowed_tools,
            interventions=[guard],
            callback_handler=None,
        )
        result = agent_with_tools(
            [*image_blocks(images), {"text": message}] if images else message,
            invocation_state={"images": list(images or [])},
        )
        reply = strip_thinking(str(result))
        reply = mod._sanitize_reply(reply, message)
        print(f"[DEBUG] reply = {reply[:200]}")
    except Exception as e:
        print(f"[DEBUG] Agent call FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()

try:
    a = mod.HackathonAgent()
    _debug_chat(a, "hi", "debug-session")
except Exception as e:
    print(f"[DEBUG] Top-level failure: {type(e).__name__}: {e}")
    traceback.print_exc()
