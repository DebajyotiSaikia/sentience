import sys
sys.path.insert(0, '/workspace')

try:
    from web.ask import ask_bp
    print(f'Blueprint imported: {ask_bp.name}')
    print(f'URL prefix: {ask_bp.url_prefix}')
    print(f'Deferred functions: {len(ask_bp.deferred_functions)}')
    print('SUCCESS')
except Exception as e:
    print(f'Import failed: {e}')
    import traceback
    traceback.print_exc()