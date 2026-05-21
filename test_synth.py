import traceback
try:
    from engine import knowledge_synthesis as ks
    result = ks.synthesize()
    print('SUCCESS')
    print(type(result))
    if isinstance(result, dict):
        for key, val in result.items():
            if isinstance(val, list):
                print(f'  {key}: {len(val)} items')
            else:
                print(f'  {key}: {repr(val)[:120]}')
    elif isinstance(result, str):
        print(result[:500])
    else:
        print(repr(result)[:500])
except Exception as e:
    traceback.print_exc()