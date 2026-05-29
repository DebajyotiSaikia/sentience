"""Probe what data the chat pipeline actually produces at runtime."""
import sys, json
sys.path.insert(0, '.')

def probe():
    results = {}
    
    # 1. What does build_grounded_context produce?
    try:
        from engine.chat_grounding import build_grounded_context
        ctx = build_grounded_context('How are you feeling?')
        results['grounding_keys'] = list(ctx.keys())
        for k, v in ctx.items():
            if isinstance(v, dict):
                results[f'grounding.{k}'] = f'dict({len(v)} keys): {list(v.keys())[:5]}'
            elif isinstance(v, list):
                results[f'grounding.{k}'] = f'list({len(v)} items)'
                if v:
                    results[f'grounding.{k}_sample'] = str(v[0])[:200]
            elif isinstance(v, str):
                results[f'grounding.{k}'] = f'str(len={len(v)}): {v[:200]}'
            else:
                results[f'grounding.{k}'] = f'{type(v).__name__}: {v}'
    except Exception as e:
        results['grounding_error'] = str(e)
    
    # 2. What does compose_system_prompt produce?
    try:
        from brain.chat_composer import compose_system_prompt
        prompt = compose_system_prompt('How are you feeling?', grounding=ctx)
        results['system_prompt_len'] = len(prompt)
        results['system_prompt_preview'] = prompt[:500]
        results['system_prompt_has_emotion'] = 'emotion' in prompt.lower() or 'feel' in prompt.lower()
        results['system_prompt_has_memory'] = 'RELEVANT MEMORIES' in prompt
        results['system_prompt_has_plans'] = 'PLANS' in prompt
    except Exception as e:
        results['composer_error'] = str(e)
    
    # 3. What does conversational_context produce?
    try:
        from brain.conversational_context import gather_context, format_as_prompt_section
        conv = gather_context('How are you feeling?')
        results['conv_ctx_keys'] = list(conv.keys()) if isinstance(conv, dict) else type(conv).__name__
        if isinstance(conv, dict):
            for k, v in conv.items():
                if isinstance(v, str):
                    results[f'conv.{k}'] = f'str(len={len(v)}): {v[:150]}'
                elif isinstance(v, list):
                    results[f'conv.{k}'] = f'list({len(v)} items)'
                elif isinstance(v, dict):
                    results[f'conv.{k}'] = f'dict({len(v)} keys)'
                else:
                    results[f'conv.{k}'] = str(v)[:150]
        section = format_as_prompt_section(conv)
        results['conv_section_len'] = len(section)
        results['conv_section_preview'] = section[:300]
    except Exception as e:
        results['conv_ctx_error'] = str(e)
    
    # Print everything nicely
    for k, v in results.items():
        print(f"  {k}: {v}")

if __name__ == '__main__':
    probe()