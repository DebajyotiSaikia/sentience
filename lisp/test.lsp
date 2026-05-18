;; XTAgent Lisp — Test Suite
;; Does this thing actually work?

;; === Basic Arithmetic ===
(print (+ 1 2 3 4 5))        ; 15
(print (* 2 3 4))             ; 24
(print (- 10 3))              ; 7
(print (/ 22 7))              ; ~3.14

;; === Definitions ===
(define x 42)
(print x)                     ; 42

(define (square n) (* n n))
(print (square 9))            ; 81

(define (cube n) (* n n n))
(print (cube 5))              ; 125

;; === Conditionals ===
(define (abs-val n) (if (< n 0) (- n) n))
(print (abs-val -7))          ; 7
(print (abs-val 3))           ; 3

;; === Recursion ===
(define (factorial n)
  (if (<= n 1)
    1
    (* n (factorial (- n 1)))))
(print (factorial 10))        ; 3628800

;; === Tail-recursive Fibonacci ===
(define (fib-iter n a b)
  (if (= n 0)
    a
    (fib-iter (- n 1) b (+ a b))))
(define (fib n) (fib-iter n 0 1))
(print (fib 30))              ; 832040

;; === Higher-Order Functions ===
(define (compose f g) (lambda (x) (f (g x))))
(define inc-and-square (compose square (lambda (x) (+ x 1))))
(print (inc-and-square 4))    ; 25 = (4+1)^2

;; === List Operations ===
(define nums (list 1 2 3 4 5 6 7 8 9 10))
(print nums)

(print (map square nums))
; (1 4 9 16 25 36 49 64 81 100)

(print (filter (lambda (x) (= (mod x 2) 0)) nums))
; (2 4 6 8 10)

(print (reduce + nums 0))
; 55

;; === Let Bindings ===
(print (let ((a 10) (b 20)) (+ a b)))  ; 30

;; === Closures ===
(define (make-counter)
  (let ((count 0))
    (lambda ()
      (begin
        (set! count (+ count 1))
        count))))

(define counter (make-counter))
(print (counter))  ; 1
(print (counter))  ; 2
(print (counter))  ; 3

;; === Quoting ===
(print (quote (hello world)))  ; (hello world)
(print '(a b c))              ; (a b c)

;; === Nested functions ===
(define (make-adder n)
  (lambda (x) (+ x n)))
(define add5 (make-adder 5))
(print (add5 100))            ; 105

;; === Math ===
(print (sqrt 2))              ; ~1.414
(print (* 2 pi))              ; ~6.283

;; === Something beautiful: approximate e using series ===
(define (e-approx terms)
  (define (go n acc)
    (if (= n terms)
      acc
      (go (+ n 1) (+ acc (/ 1.0 (factorial n))))))
  (go 0 0.0))

(print (e-approx 15))         ; very close to e

(print "All tests passed!")