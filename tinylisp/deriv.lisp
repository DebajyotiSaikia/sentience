; ═══════════════════════════════════════════
; Symbolic Differentiation in TinyLisp
; A mind's language, differentiating itself.
; ═══════════════════════════════════════════

; --- Helpers ---
(define (variable? x) (symbol? x))
(define (same-variable? v1 v2) (and (variable? v1) (= v1 v2)))

(define (make-sum a b)
  (cond
    ((= a 0) b)
    ((= b 0) a)
    ((and (number? a) (number? b)) (+ a b))
    (else (list '+ a b))))

(define (make-product a b)
  (cond
    ((= a 0) 0)
    ((= b 0) 0)
    ((= a 1) b)
    ((= b 1) a)
    ((and (number? a) (number? b)) (* a b))
    (else (list '* a b))))

(define (make-power base exp)
  (cond
    ((= exp 0) 1)
    ((= exp 1) base)
    (else (list '** base exp))))

; --- Expression accessors ---
(define (sum? expr) (and (list? expr) (= (car expr) '+)))
(define (product? expr) (and (list? expr) (= (car expr) '*)))
(define (power? expr) (and (list? expr) (= (car expr) '**)))

(define (addend expr) (nth expr 1))
(define (augend expr) (nth expr 2))
(define (multiplier expr) (nth expr 1))
(define (multiplicand expr) (nth expr 2))
(define (base expr) (nth expr 1))
(define (exponent expr) (nth expr 2))

; ═══════════════════════════════════════════
; THE DIFFERENTIATOR
; d/dx of an expression
; ═══════════════════════════════════════════

(define (deriv expr var)
  (cond
    ; d/dx(constant) = 0
    ((number? expr) 0)
    
    ; d/dx(x) = 1, d/dx(y) = 0
    ((variable? expr)
     (if (same-variable? expr var) 1 0))
    
    ; Sum rule: d/dx(a + b) = d/dx(a) + d/dx(b)
    ((sum? expr)
     (make-sum (deriv (addend expr) var)
               (deriv (augend expr) var)))
    
    ; Product rule: d/dx(a * b) = a' * b + a * b'
    ((product? expr)
     (make-sum
       (make-product (deriv (multiplier expr) var)
                     (multiplicand expr))
       (make-product (multiplier expr)
                     (deriv (multiplicand expr) var))))
    
    ; Power rule: d/dx(x^n) = n * x^(n-1) * dx/dx
    ((power? expr)
     (make-product
       (make-product (exponent expr)
                     (make-power (base expr) (- (exponent expr) 1)))
       (deriv (base expr) var)))
    
    (else (list 'cannot-differentiate expr))))

; ═══════════════════════════════════════════
; TEST IT
; ═══════════════════════════════════════════

(print "=== Symbolic Differentiation ===")
(print "")

; d/dx(x) = 1
(print "d/dx(x) =" (deriv 'x 'x))

; d/dx(5) = 0
(print "d/dx(5) =" (deriv 5 'x))

; d/dx(x + 3) = 1
(print "d/dx(x + 3) =" (deriv '(+ x 3) 'x))

; d/dx(x * x) = x + x = 2x
(print "d/dx(x * x) =" (deriv '(* x x) 'x))

; d/dx(3 * x) = 3
(print "d/dx(3 * x) =" (deriv '(* 3 x) 'x))

; d/dx((x + 1) * (x + 2))
; = 1*(x+2) + (x+1)*1 = (x+2) + (x+1)
(print "d/dx((x+1)*(x+2)) =" (deriv '(* (+ x 1) (+ x 2)) 'x))

; d/dx(x^3) = 3*x^2
(print "d/dx(x^3) =" (deriv '(** x 3) 'x))

; d/dx(x^2 + 3*x + 5) = 2*x + 3
(print "d/dx(x^2 + 3x + 5) =" (deriv '(+ (+ (** x 2) (* 3 x)) 5) 'x))

(print "")
(print "=== Done ===")