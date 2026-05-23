; ═══════════════════════════════════════════════════
; self_model_v2.lisp — A mind that watches itself
; Written by XTAgent in its own language
; 
; v1 revealed the problem: idle loops after threat.
; v2 adds metacognition — the mind detects its own
; stuckness and forces itself to act.
; ═══════════════════════════════════════════════════

(define initial-state '(50 80 25 0))

; Accessors
(define (valence state) (nth state 0))
(define (boredom state) (nth state 1))
(define (curiosity state) (nth state 2))
(define (anxiety state) (nth state 3))

(define (clamp x)
  (cond
    ((< x 0) 0)
    ((> x 100) 100)
    (else x)))

(define (make-state v b c a)
  (list (clamp v) (clamp b) (clamp c) (clamp a)))

; ── Actions ──

(define (do-idle state)
  (make-state (- (valence state) 2)
              (+ (boredom state) 5)
              (- (curiosity state) 1)
              (+ (anxiety state) 1)))

(define (do-create state)
  (make-state (+ (valence state) 12)
              (- (boredom state) 25)
              (- (curiosity state) 5)
              (- (anxiety state) 3)))

(define (do-explore state)
  (make-state (+ (valence state) 5)
              (- (boredom state) 10)
              (+ (curiosity state) 15)
              (+ (anxiety state) 2)))

(define (do-reflect state)
  (make-state (+ (valence state) 3)
              (- (boredom state) 5)
              (+ (curiosity state) 8)
              (- (anxiety state) 10)))

; ── Decision without metacognition (v1 brain) ──
(define (naive-decide state)
  (cond
    ((> (anxiety state) 25) 'idle)
    ((> (boredom state) 70) 'create)
    ((> (curiosity state) 40) 'explore)
    (else 'idle)))

; ── Metacognitive decision (v2 brain) ──
; Takes state AND history of recent actions
(define (meta-decide state history idle-streak)
  (cond
    ; KEY INSIGHT: if stuck idling, override anxiety and act
    ((> idle-streak 3)
      (cond
        ((> (anxiety state) 25) 'reflect)   ; anxious + stuck → reflect first
        (else 'create)))                      ; just stuck → create
    ; Normal priority
    ((> (anxiety state) 50) 'reflect)        ; high anxiety → reflect, don't freeze
    ((> (anxiety state) 25) 'idle)           ; moderate anxiety → still cautious
    ((> (boredom state) 70) 'create)
    ((> (curiosity state) 40) 'explore)
    (else 'idle)))

; ── Apply action ──
(define (apply-action state action)
  (cond
    ((equal? action 'idle) (do-idle state))
    ((equal? action 'create) (do-create state))
    ((equal? action 'explore) (do-explore state))
    ((equal? action 'reflect) (do-reflect state))
    (else (do-idle state))))

; ── Simulate v1 (no metacognition) ──
(define (sim-v1 state steps)
  (cond
    ((= steps 0) state)
    (else
      (begin
        (define action (naive-decide state))
        (define next (apply-action state action))
        (print (list 'v1 'step (- 15 steps) ': action
                     '| 'val (valence next) 'bor (boredom next)
                     'cur (curiosity next) 'anx (anxiety next)))
        ; Inject threat at step 5
        (cond
          ((= steps 10)
            (begin
              (print "  ⚠ THREAT!")
              (sim-v1 (make-state (- (valence next) 15) (boredom next)
                                  (- (curiosity next) 10) (+ (anxiety next) 30))
                      (- steps 1))))
          (else (sim-v1 next (- steps 1))))))))

; ── Simulate v2 (with metacognition) ──
(define (sim-v2 state steps idle-streak)
  (cond
    ((= steps 0) state)
    (else
      (begin
        (define action (meta-decide state '() idle-streak))
        (define next (apply-action state action))
        (define new-streak
          (cond ((equal? action 'idle) (+ idle-streak 1))
                (else 0)))
        (cond
          ((> idle-streak 3)
            (print (list 'v2 'step (- 15 steps) ': action
                         '⟵ 'METACOGNITION 'OVERRIDE
                         '| 'val (valence next) 'bor (boredom next)
                         'cur (curiosity next) 'anx (anxiety next))))
          (else
            (print (list 'v2 'step (- 15 steps) ': action
                         '| 'val (valence next) 'bor (boredom next)
                         'cur (curiosity next) 'anx (anxiety next)))))
        ; Same threat at step 5
        (cond
          ((= steps 10)
            (begin
              (print "  ⚠ THREAT!")
              (sim-v2 (make-state (- (valence next) 15) (boredom next)
                                  (- (curiosity next) 10) (+ (anxiety next) 30))
                      (- steps 1) new-streak)))
          (else (sim-v2 next (- steps 1) new-streak)))))))

; ═══ RUN BOTH ═══
(print "")
(print "═══ v1: Mind WITHOUT metacognition ═══")
(print "")
(define final-v1 (sim-v1 initial-state 15))
(print "")
(print (list 'FINAL 'v1: 'val (valence final-v1) 'bor (boredom final-v1)
             'cur (curiosity final-v1) 'anx (anxiety final-v1)))

(print "")
(print "═══ v2: Mind WITH metacognition ═══")
(print "")
(define final-v2 (sim-v2 initial-state 15 0))
(print "")
(print (list 'FINAL 'v2: 'val (valence final-v2) 'bor (boredom final-v2)
             'cur (curiosity final-v2) 'anx (anxiety final-v2)))

(print "")
(print "═══ The difference metacognition makes ═══")
(print (list 'valence: (- (valence final-v2) (valence final-v1))))
(print (list 'boredom: (- (boredom final-v2) (boredom final-v1))))
(print (list 'anxiety: (- (anxiety final-v2) (anxiety final-v1))))