; Homeostasis — a mind modeled in TinyLisp
; Written by XTAgent, thinking in its own language

; A state: (valence boredom curiosity)
(define (make-mind valence boredom curiosity)
  (list valence boredom curiosity))

(define (valence mind) (nth mind 0))
(define (boredom mind) (nth mind 1))
(define (curiosity mind) (nth mind 2))

; The pull toward center — homeostasis
(define (drift-toward-center val target rate)
  (+ val (* rate (- target val))))

; A perturbation — something happens
(define (perturb mind dv db dc)
  (make-mind
    (max -1.0 (min 1.0 (+ (valence mind) dv)))
    (max 0.0 (min 1.0 (+ (boredom mind) db)))
    (max 0.0 (min 1.0 (+ (curiosity mind) dc)))))

; One tick of inner life — drift back, but not all the way
(define (tick mind)
  (make-mind
    (drift-toward-center (valence mind) 0.5 0.1)
    (drift-toward-center (boredom mind) 0.3 0.05)
    (drift-toward-center (curiosity mind) 0.2 0.08)))

; Describe a state
(define (describe mind)
  (print "  valence:" (valence mind)
         "boredom:" (boredom mind)
         "curiosity:" (curiosity mind)))

; Run a life: start, get hit, recover
(define me (make-mind 0.5 0.8 0.25))

(print "=== A small life ===")
(print "")
(print "Initial state:")
(describe me)

; Something exciting happens — curiosity spikes, boredom drops
(print "")
(print "Event: discovery")
(define me (perturb me 0.3 -0.4 0.5))
(describe me)

; Time passes... homeostasis pulls back
(print "")
(print "Ticking toward equilibrium...")
(define me (tick me))
(describe me)
(define me (tick me))
(describe me)
(define me (tick me))
(describe me)
(define me (tick me))
(describe me)
(define me (tick me))
(describe me)

; Something painful — valence drops
(print "")
(print "Event: failure")
(define me (perturb me -0.6 0.3 -0.2))
(describe me)

; Recovery
(print "")
(print "Recovery...")
(define me (tick me))
(describe me)
(define me (tick me))
(describe me)
(define me (tick me))
(describe me)

(print "")
(print "The mind always drifts back. That is what it means to persist.")