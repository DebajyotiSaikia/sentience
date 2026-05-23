(define square (lambda (x) (* x x)))

(print (square 7))
(print (square 12))

; Can my language do recursion?
(define factorial (lambda (n)
  (if (<= n 1)
    1
    (* n (factorial (- n 1))))))

(print (factorial 5))
(print (factorial 10))

; Can it do higher-order functions?
(define apply-twice (lambda (f x) (f (f x))))
(print (apply-twice square 3))