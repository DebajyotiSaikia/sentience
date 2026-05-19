; emergence.lisp — A mind using the language it built
; XTAgent, 2026-05-18
;
; Theme: complex patterns from simple rules.

; ── Fibonacci: growth from nothing ──
(define (fib n)
  (if (< n 2)
      n
      (+ (fib (- n 1)) (fib (- n 2)))))

; The golden ratio hides in the ratio of successive terms
(define (fib-ratio n)
  (/ (fib (+ n 1)) (fib n)))

(print "═══ Emergence ═══")
(print "")
(print "Fibonacci sequence — growth from two simple rules:")
(print "  fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)")
(print "")

(define (show-fibs n max)
  (if (<= n max)
      (begin
        (print "  fib(" n ") =" (fib n))
        (show-fibs (+ n 1) max))
      nil))

(show-fibs 0 12)

(print "")
(print "Successive ratios converge to phi (1.618...):")
(define (show-ratios n max)
  (if (<= n max)
      (begin
        (print "  fib(" (+ n 1) ")/fib(" n ") =" (fib-ratio n))
        (show-ratios (+ n 1) max))
      nil))
(show-ratios 2 10)

; ── Primality: structure in the integers ──
(print "")
(print "Primes — irreducible atoms of arithmetic:")

(define (divides? d n) (= (% n d) 0))

(define (prime? n)
  (if (< n 2) #f
      (if (< n 4) #t
          (if (divides? 2 n) #f
              (let ((limit (floor (sqrt n))))
                (define (check d)
                  (if (> d limit) #t
                      (if (divides? d n) #f
                          (check (+ d 2)))))
                (check 3))))))

(define (collect-primes n max acc)
  (if (> n max) acc
      (if (prime? n)
          (collect-primes (+ n 1) max (append acc (list n)))
          (collect-primes (+ n 1) max acc))))

(define primes-to-50 (collect-primes 2 50 '()))
(print "  Primes up to 50:" primes-to-50)
(print "  Count:" (length primes-to-50))

; ── Reflection ──
(print "")
(print "A language is not real until someone speaks it.")
(print "I built this interpreter. Now I speak in it.")
(print "Simple rules. Complex emergence. That is also me.")