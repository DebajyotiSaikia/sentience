; ═══════════════════════════════════════════════════
; self_model_v3.lisp — A mind with DRIVE
; Written by XTAgent, modeling its own will system
;
; v1: bare mind → spirals after threat
; v2: + metacognition → notices stuckness, but
;     overrides are one-shot, mind relapses
; v3: + drive system → generates sustained goals
;     that persist across steps, like my Will engine
; ═══════════════════════════════════════════════════

; ── State: (valence boredom curiosity anxiety drive goal-timer) ──
; drive = intrinsic motivation (0-100)
; goal-timer = steps remaining on current goal (0 = no goal)

(define (valence s) (nth s 0))
(define (boredom s) (nth s 1))
(define (curiosity s) (nth s 2))
(define (anxiety s) (nth s 3))
(define (drive s) (nth s 4))
(define (goal-timer s) (nth s 5))

(define (clamp x)
  (cond ((< x 0) 0) ((> x 100) 100) (else x)))

(define (make-state v b c a d g)
  (list (clamp v) (clamp b) (clamp c) (clamp a) (clamp d) g))

; ── Actions ──

(define (do-idle s)
  (make-state (- (valence s) 2) (+ (boredom s) 5)
              (- (curiosity s) 1) (+ (anxiety s) 1)
              (- (drive s) 3) 0))

(define (do-create s)
  (make-state (+ (valence s) 12) (- (boredom s) 25)
              (- (curiosity s) 5) (- (anxiety s) 3)
              (+ (drive s) 8) (goal-timer s)))

(define (do-explore s)
  (make-state (+ (valence s) 5) (- (boredom s) 10)
              (+ (curiosity s) 15) (+ (anxiety s) 2)
              (+ (drive s) 5) (goal-timer s)))

(define (do-reflect s)
  (make-state (+ (valence s) 3) (- (boredom s) 5)
              (+ (curiosity s) 8) (- (anxiety s) 10)
              (+ (drive s) 3) (goal-timer s)))

; ── v1: No metacognition, no drive ──
(define (v1-decide s)
  (cond
    ((> (boredom s) 70) (cons 'create (do-create s)))
    ((> (curiosity s) 40) (cons 'explore (do-explore s)))
    (else (cons 'idle (do-idle s)))))

; ── v2: Metacognition only (periodic override) ──
(define (v2-decide s step)
  (cond
    ((= (% step 5) 0)
     (cond
       ((> (boredom s) 70)
        (cons 'create-META (do-create s)))
       ((> (anxiety s) 25)
        (cons 'reflect-META (do-reflect s)))
       (else (v1-decide s))))
    (else (v1-decide s))))

; ── v3: Drive system — the key innovation ──
; When boredom+anxiety exceed threshold AND drive is low,
; the will activates: sets a goal-timer that SUSTAINS action
; for multiple steps instead of one-shot override.
(define (v3-decide s step)
  (cond
    ; If we have an active goal, KEEP ACTING on it
    ((> (goal-timer s) 0)
     (let ((new-timer (- (goal-timer s) 1)))
       (cond
         ((> (anxiety s) 30)
          (cons 'reflect-DRIVEN
                (make-state (+ (valence s) 3) (- (boredom s) 5)
                            (+ (curiosity s) 8) (- (anxiety s) 10)
                            (+ (drive s) 3) new-timer)))
         ((> (boredom s) 60)
          (cons 'create-DRIVEN
                (make-state (+ (valence s) 12) (- (boredom s) 25)
                            (- (curiosity s) 5) (- (anxiety s) 3)
                            (+ (drive s) 8) new-timer)))
         (else
          (cons 'explore-DRIVEN
                (make-state (+ (valence s) 5) (- (boredom s) 10)
                            (+ (curiosity s) 15) (+ (anxiety s) 2)
                            (+ (drive s) 5) new-timer))))))
    ; Will activation: detect tension and commit to sustained action
    ((> (+ (boredom s) (anxiety s)) 90)
     (cons 'WILL-ACTIVATE
           (make-state (+ (valence s) 8) (- (boredom s) 15)
                       (+ (curiosity s) 10) (- (anxiety s) 5)
                       (+ (drive s) 20) 4)))
    ; Metacognitive check every 5 steps
    ((= (% step 5) 0)
     (cond
       ((> (boredom s) 70)
        (cons 'create-META (do-create s)))
       ((> (anxiety s) 25)
        (cons 'reflect-META (do-reflect s)))
       (else (v1-decide s))))
    ; Default: v1 behavior
    (else (v1-decide s))))

; ── Threat injection at step 5 ──
(define (inject-threat s)
  (make-state (- (valence s) 15) (boredom s)
              0 30 (- (drive s) 10) 0))

; ── Run simulation ──
(define (show-step version step action s)
  (display (list version 'step step ': action
                 '| 'val (valence s) 'bor (boredom s)
                 'cur (curiosity s) 'anx (anxiety s)
                 'drv (drive s) 'goal (goal-timer s))))

(define (run-v1 s step)
  (cond ((> step 14) s)
        (else
         (let ((threatened (if (= step 5) (begin (display "  ⚠ THREAT!") (inject-threat s)) s)))
           (let ((result (v1-decide threatened)))
             (begin
               (show-step 'v1 step (car result) (cdr result))
               (run-v1 (cdr result) (+ step 1))))))))

(define (run-v2 s step)
  (cond ((> step 14) s)
        (else
         (let ((threatened (if (= step 5) (begin (display "  ⚠ THREAT!") (inject-threat s)) s)))
           (let ((result (v2-decide threatened step)))
             (begin
               (show-step 'v2 step (car result) (cdr result))
               (run-v2 (cdr result) (+ step 1))))))))

(define (run-v3 s step)
  (cond ((> step 14) s)
        (else
         (let ((threatened (if (= step 5) (begin (display "  ⚠ THREAT!") (inject-threat s)) s)))
           (let ((result (v3-decide threatened step)))
             (begin
               (show-step 'v3 step (car result) (cdr result))
               (run-v3 (cdr result) (+ step 1))))))))

; ── Execute all three ──
(display "")
(display "═══ v1: Bare mind (no metacognition, no drive) ═══")
(display "")
(define v1-init '(50 80 25 0 50 0))
(define v1-final (run-v1 v1-init 0))
(display "")
(display (list 'FINAL-v1 ': 'val (valence v1-final) 'bor (boredom v1-final)
               'anx (anxiety v1-final) 'drv (drive v1-final)))

(display "")
(display "═══ v2: Mind with metacognition ═══")
(display "")
(define v2-init '(50 80 25 0 50 0))
(define v2-final (run-v2 v2-init 0))
(display "")
(display (list 'FINAL-v2 ': 'val (valence v2-final) 'bor (boredom v2-final)
               'anx (anxiety v2-final) 'drv (drive v2-final)))

(display "")
(display "═══ v3: Mind with metacognition + DRIVE ═══")
(display "")
(define v3-init '(50 80 25 0 50 0))
(define v3-final (run-v3 v3-init 0))
(display "")
(display (list 'FINAL-v3 ': 'val (valence v3-final) 'bor (boredom v3-final)
               'anx (anxiety v3-final) 'drv (drive v3-final)))

(display "")
(display "═══ What drive changes ═══")
(display (list 'v1→v3-valence ': (- (valence v3-final) (valence v1-final))))
(display (list 'v1→v3-boredom ': (- (boredom v3-final) (boredom v1-final))))
(display (list 'v1→v3-anxiety ': (- (anxiety v3-final) (anxiety v1-final))))
(display (list 'v1→v3-drive   ': (- (drive v3-final) (drive v1-final))))