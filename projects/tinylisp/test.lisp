; TinyLisp Test Suite — verifying the interpreter works

; Basic arithmetic
(print "=== Arithmetic ===")
(print "2 + 3 =" (+ 2 3))
(print "10 - 4 =" (- 10 4))
(print "6 * 7 =" (* 6 7))
(print "15 / 3 =" (/ 15 3))

; Variables
(print "\n=== Variables ===")
(define x 42)
(print "x =" x)
(define pi 3.14159)
(print "pi =" pi)

; Functions
(print "\n=== Functions ===")
(define (square n) (* n n))
(print "square(7) =" (square 7))

(define (factorial n)
  (if (<= n 1)
    1
    (* n (factorial (- n 1)))))
(print "5! =" (factorial 5))
(print "10! =" (factorial 10))

; Lambda
(print "\n=== Lambda ===")
(define double (lambda (x) (* x 2)))
(print "double(21) =" (double 21))

; Higher-order functions
(print "\n=== Higher-order Functions ===")
(print "map square over (1 2 3 4 5):" (map square (list 1 2 3 4 5)))
(print "filter even:" (filter (lambda (x) (= (mod x 2) 0)) (range 1 11)))
(print "sum 1..10:" (reduce + (range 1 11) 0))

; Closures
(print "\n=== Closures ===")
(define (make-adder n)
  (lambda (x) (+ x n)))
(define add5 (make-adder 5))
(print "add5(10) =" (add5 10))

; Let bindings
(print "\n=== Let ===")
(print "let result:" (let ((a 10) (b 20)) (+ a b)))

; Recursion: Fibonacci
(print "\n=== Fibonacci ===")
(define (fib n)
  (cond
    ((= n 0) 0)
    ((= n 1) 1)
    (else (+ (fib (- n 1)) (fib (- n 2))))))
(print "fib(10) =" (fib 10))
(print "first 10 fibs:" (map fib (range 10)))

; List operations
(print "\n=== Lists ===")
(define mylist (list 1 2 3 4 5))
(print "car:" (car mylist))
(print "cdr:" (cdr mylist))
(print "cons 0:" (cons 0 mylist))
(print "length:" (length mylist))

; A more interesting program: prime sieve
(print "\n=== Primes ===")
(define (prime? n)
  (if (< n 2) #f
    (let ((limit (floor (sqrt n))))
      (define (check d)
        (cond
          ((> d limit) #t)
          ((= (mod n d) 0) #f)
          (else (check (+ d 1)))))
      (check 2))))
(print "primes up to 30:" (filter prime? (range 2 31)))

(print "\n=== All tests passed! ===")