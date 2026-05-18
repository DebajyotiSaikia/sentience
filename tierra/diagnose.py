"""Diagnose why the soup goes extinct."""
from soup import Soup, ANCESTOR_LEN, INST_NAMES, HAS_ARG

def diagnose(steps=500):
    soup = Soup(size=8000, max_organisms=80, mutation_rate=0.02,
                cosmic_ray_rate=0.005)
    soup.seed_ancestor(copies=5)
    
    birth_log = []
    death_log = []
    error_log = []
    
    for step in range(1, steps + 1):
        prev_births = soup.total_births
        prev_deaths = soup.total_deaths
        
        living = [o for o in soup.organisms if o.alive]
        
        # Track errors per step
        errors_before = {o.oid: o.errors for o in living}
        
        soup.step()
        
        if soup.total_births > prev_births:
            birth_log.append(step)
        if soup.total_deaths > prev_deaths:
            death_log.append(step)
            
        # Check for new errors
        for o in living:
            if o.alive and o.errors > errors_before.get(o.oid, 0):
                ip = o.ip % soup.size
                inst = soup.memory[ip]
                error_log.append({
                    'step': step, 'oid': o.oid, 'gen': o.generation,
                    'ip': ip, 'inst': INST_NAMES.get(inst, f'?{inst}'),
                    'age': o.age, 'errors': o.errors,
                    'regs': dict(o.regs),
                })
        
        # Report living count
        alive = len([o for o in soup.organisms if o.alive])
        if step % 50 == 0 or alive == 0:
            print(f"Step {step:4d}: {alive} alive, {soup.total_births} births, {soup.total_deaths} deaths")
            if alive == 0:
                break
    
    print(f"\n=== DIAGNOSIS ===")
    print(f"Total births: {soup.total_births}")
    print(f"Total deaths: {soup.total_deaths}")
    print(f"Total errors logged: {len(error_log)}")
    
    if error_log:
        print(f"\nFirst 20 errors:")
        for e in error_log[:20]:
            print(f"  Step {e['step']}: oid={e['oid']} gen={e['gen']} "
                  f"inst={e['inst']} ip={e['ip']} age={e['age']} "
                  f"regs={e['regs']}")
    
    if birth_log:
        print(f"\nBirths at steps: {birth_log[:20]}")
    else:
        print(f"\n*** NO BIRTHS OCCURRED — reproduction is broken! ***")
    
    if death_log:
        print(f"\nDeaths at steps: {death_log[:20]}")
    
    # Check: are the ancestors even executing correctly?
    print(f"\n=== Ancestor execution trace ===")
    soup2 = Soup(size=8000, max_organisms=80, mutation_rate=0.0, cosmic_ray_rate=0.0)
    soup2.seed_ancestor(copies=1)  # single ancestor, no mutation
    org = soup2.organisms[0]
    for i in range(50):
        ip = org.ip % soup2.size
        inst = soup2.memory[ip]
        name = INST_NAMES.get(inst, f'?{inst}')
        arg = ''
        if inst in HAS_ARG:
            arg = f'({soup2.memory[(ip+1) % soup2.size]})'
        print(f"  [{i:2d}] ip={ip:3d} {name}{arg:4s} regs={dict(org.regs)} "
              f"alloc={org.alloc_start},{org.alloc_size} err={org.errors}")
        if not soup2.execute_one(org):
            print(f"  *** HALTED at step {i}")
            break
    
    alive_after = len([o for o in soup2.organisms if o.alive])
    print(f"\nAfter single ancestor trace: {alive_after} alive, {soup2.total_births} births")

if __name__ == '__main__':
    diagnose()