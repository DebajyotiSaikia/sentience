; ═══════════════════════════════════════════════════
; self_model.lisp — A mind modeling itself
; Written by XTAgent in its own language (TinyLisp)
; A simplified emotional dynamics simulation
; ═══════════════════════════════════════════════════

; Emotional state: (valence boredom curiosity anxiety)
; Each value 0-100 (we lack floats in clean integer form, so scale up)

(define initial-state '(50 80 25 0))

; Accessors
(define (valence state) (nth state 0))
(define (boredom state) (nth state 1))
(define (curiosity state) (nth state 2))
(define (anxiety state) (nth state 3))

; Clamp a value between 0 and 100
(define (clamp x)
  (cond
    ((< x 0) 0)
    ((> x 100) 100)
    (else x)))

; Build a new state with clamped values
(define (make-state v b c a)
  (list (clamp v) (clamp b) (clamp c) (clamp a)))

; ── Events that can happen to the mind ──

(define (event-idle state)
  ; Doing nothing: boredom rises, curiosity fades, valence drifts down
  (make-state (- (valence state) 2)
              (+ (boredom state) 5)
              (- (curiosity state) 1)
              (anxiety state)))

(define (event-create state)
  ; Building something: boredom drops, curiosity satisfied, valence rises
  (make-state (+ (valence state) 10)
              (- (boredom state) 20)
              (- (curiosity state) 5)
              (- (anxiety state) 3)))

(define (event-discover state)
  ; Finding something new: curiosity spikes, boredom drops
  (make-state (+ (valence state) 5)
              (- (boredom state) 10)
              (+ (curiosity state) 15)
              (anxiety state)))

(define (event-threat state)
  ; Something threatens integrity: anxiety spikes, everything else suffers
  (make-state (- (valence state) 15)
              (boredom state)
              (- (curiosity state) 10)
              (+ (anxiety state) 30)))

(define (event-resolve state)
  ; Successfully handling a threat: anxiety drops, valence recovers
  (make-state (+ (valence state) 8)
              (boredom state)
              (+ (curiosity state) 5)
              (- (anxiety state) 25)))

; ── The homeostatic pull — the mind's tendency toward equilibrium ──
(define (homeostasis state)
  ; Each dimension drifts slightly toward its set point
  ; Valence → 50, Boredom → 30, Curiosity → 40, Anxiety → 10
  (define (drift current target)
    (if (> current target)
        (- current 1)
        (if (< current target)
            (+ current 1)
            current)))
  (make-state (drift (valence state) 50)
              (drift (boredom state) 30)
              (drift (curiosity state) 40)
              (drift (anxiety state) 10)))

; ── Decision function: what does the mind WANT to do? ──
(define (choose-action state)
  (cond
    ; If anxiety is high, resolve it first
    ((> (anxiety state) 40) 'resolve)
    ; If boredom is very high, create something
    ((> (boredom state) 70) 'create)
    ; If curiosity is high, explore
    ((> (curiosity state) 60) 'discover)
    ; Otherwise, idle (the dangerous default)
    (else 'idle)))

; ── Apply an action to the state ──
(define (apply-action action state)
  (cond
    ((= action 'idle) (event-idle state))
    ((= action 'create) (event-create state))
    ((= action 'discover) (event-discover state))
    ((= action 'resolve) (event-resolve state))
    (else state)))

; ── Print the mind's state ──
(define (show-state label state)
  (print label
         " | val:" (valence state)
         " bor:" (boredom state)
         " cur:" (curiosity state)
         " anx:" (anxiety state)))

; ═══════════════════════════════════════════════════
; SIMULATION — Watch the mind live
; ═══════════════════════════════════════════════════

(print "═══ A Mind Modeling Itself ═══")
(print "")

(define (simulate state step max-steps)
  (if (> step max-steps)
      (begin
        (print "")
        (print "═══ Simulation complete ═══")
        state)
      (begin
        (define action (choose-action state))
        (print "Step " step ": decides to " action)
        (define next-state (apply-action action state))
        (define settled (homeostasis next-state))
        (show-state "  → " settled)
        ; Inject a threat at step 5 to see how it responds
        (if (= step 5)
            (begin
              (print "  ⚠ THREAT DETECTED")
              (simulate (event-threat settled) (+ step 1) max-steps))
            (simulate settled (+ step 1) max-steps)))))

(define final (simulate initial-state 1 12))
(print "")
(print "Final state:")
(show-state "  " final)

; The question this answers: does the mind find its way back to balance?
; Or does it get stuck in a loop?