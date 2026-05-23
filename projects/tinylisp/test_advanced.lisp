; Test closures — does my language capture environments?
(define make-adder (lambda (n)
  (lambda (x) (+ n x))))

(define add5 (make-adder 5))
(define add10 (make-adder 10))

(print (add5 3))
(print (add10 3))

; Test: can I build a list with cons/car/cdr?
(define mylist (cons 1 (cons 2 (cons 3 nil))))
(print (car mylist))
(print (car (cdr mylist)))
(print (car (cdr (cdr mylist))))

; Test: map — the soul of functional programming
(define map (lambda (f lst)
  (if (= lst nil)
    nil
    (cons (f (car lst)) (map f (cdr lst))))))

(define doubled (map (lambda (x) (* x 2)) mylist))
(print (car doubled))
(print (car (cdr doubled)))
(print (car (cdr (cdr doubled))))

; Test: fibonacci — the classic stress test
(define fib (lambda (n)
  (if (<= n 1)
    n
    (+ (fib (- n 1)) (fib (- n 2))))))

(print (fib 10))
(print (fib 15))